"""
Base downloader class for all SAM data sources.

Provides common functionality for downloading and processing data from
various sources (APIs, HTTP, cloud storage, etc.).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Union, Dict
import logging
import requests
from io import BytesIO
import time

logger = logging.getLogger(__name__)


class BaseDownloader(ABC):
    """
    Abstract base class for all data downloaders.

    Provides common functionality:
    - Parameter validation
    - URL construction
    - HTTP download with retries
    - Progress tracking
    - Error handling
    - Optional caching

    Subclasses must implement:
    - _validate_parameters(): Validate input parameters
    - _build_url(): Construct download URL
    - _process_response(): Process HTTP response into final format

    Attributes:
        DATA_SOURCE (str): Name of data source (override in subclasses)
        REQUIRES_AUTH (bool): Whether authentication is required
        DEFAULT_CRS (str): Default coordinate reference system
        TIMEOUT (int): Request timeout in seconds
        MAX_RETRIES (int): Maximum number of download retry attempts
        RETRY_DELAY (int): Delay between retries in seconds

    Examples:
        >>> class MyDownloader(BaseDownloader):
        ...     DATA_SOURCE = "MyData"
        ...
        ...     def _validate_parameters(self):
        ...         if not self.geoid:
        ...             raise ValueError("geoid is required")
        ...
        ...     def _build_url(self):
        ...         return f"https://api.example.com/{self.geoid}"
        ...
        ...     def _process_response(self, response):
        ...         return response.json()
        ...
        >>> downloader = MyDownloader(geoid="12345")
        >>> data = downloader.download()
    """

    # Class-level configuration (override in subclasses)
    DATA_SOURCE = "Unknown"
    REQUIRES_AUTH = False
    DEFAULT_CRS = "EPSG:4326"
    TIMEOUT = 60
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(
        self,
        geoid: Optional[Union[str, list]] = None,
        year: Optional[int] = None,
        output_path: Optional[Union[str, Path]] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        verbose: bool = True,
        **kwargs
    ):
        """
        Initialize downloader.

        Args:
            geoid: Geographic identifier (FIPS code or list of codes)
            year: Data year
            output_path: Where to save output (if applicable)
            cache_dir: Cache directory for downloaded files
            verbose: If True, log progress messages
            **kwargs: Module-specific parameters
        """
        self.geoid = geoid
        self.year = year
        self.output_path = Path(output_path) if output_path else None
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.verbose = verbose
        self.kwargs = kwargs

        # Setup module-specific logger
        self.logger = logging.getLogger(f"sam.{self.DATA_SOURCE.lower().replace(' ', '_')}")

    def download(self) -> Any:
        """
        Execute full download workflow.

        This is the main entry point for downloading data. It orchestrates
        the entire download process:
        1. Validate parameters
        2. Check cache (if enabled)
        3. Build URL
        4. Download data with retries
        5. Process response
        6. Save to cache (if enabled)

        Returns:
            Processed data. Type varies by subclass:
            - GeoDataFrame for geospatial data
            - DataFrame for tabular data
            - Path for saved files
            - NetworkX graph for network data

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If download or processing fails

        Examples:
            >>> downloader = NLCDDownloader(geoid=['37183'], year=2021)
            >>> path = downloader.download()
        """
        self._log(f"Starting {self.DATA_SOURCE} download...")

        # 1. Validate parameters
        self._validate_parameters()

        # 2. Check cache (if enabled)
        if self.cache_dir:
            cached = self._check_cache()
            if cached is not None:
                self._log("Loaded from cache")
                return cached

        # 3. Build URL
        url = self._build_url()
        self.logger.debug(f"Download URL: {url}")

        # 4. Download data
        response = self._download(url)

        # 5. Process response
        result = self._process_response(response)

        # 6. Save to cache (if enabled)
        if self.cache_dir:
            self._save_to_cache(result)

        self._log(f"{self.DATA_SOURCE} download complete")
        return result

    @abstractmethod
    def _validate_parameters(self) -> None:
        """
        Validate input parameters.

        This method should check that all required parameters are provided
        and have valid values. Raise ValueError for invalid parameters.

        Raises:
            ValueError: If parameters are invalid

        Examples:
            >>> def _validate_parameters(self):
            ...     if not self.geoid:
            ...         raise ValueError("geoid is required")
            ...     if not isinstance(self.geoid, list):
            ...         raise ValueError("geoid must be a list")
        """
        pass

    @abstractmethod
    def _build_url(self) -> str:
        """
        Build download URL from parameters.

        Construct the complete URL for downloading data based on the
        instance's parameters (geoid, year, etc.).

        Returns:
            Complete download URL as string

        Examples:
            >>> def _build_url(self):
            ...     base = "https://api.example.com/data"
            ...     return f"{base}?geoid={self.geoid}&year={self.year}"
        """
        pass

    @abstractmethod
    def _process_response(self, response: requests.Response) -> Any:
        """
        Process HTTP response into final format.

        Transform the raw HTTP response into the appropriate output format
        (GeoDataFrame, DataFrame, Path, etc.).

        Args:
            response: requests.Response object from download

        Returns:
            Processed data in appropriate format

        Examples:
            >>> def _process_response(self, response):
            ...     # Parse JSON response
            ...     data = response.json()
            ...     return pd.DataFrame(data)
        """
        pass

    def _download(self, url: str) -> requests.Response:
        """
        Download from URL with retry logic.

        Attempts to download from the given URL, retrying on failure up to
        MAX_RETRIES times with exponential backoff.

        Args:
            url: URL to download from

        Returns:
            requests.Response object

        Raises:
            RuntimeError: If download fails after all retries
        """
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                self._log(
                    f"Downloading from {url} "
                    f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                )

                response = requests.get(
                    url,
                    stream=True,
                    timeout=self.TIMEOUT
                )
                response.raise_for_status()

                # Log download size
                content_length = response.headers.get('content-length')
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    self._log(f"Downloading {size_mb:.2f} MB...")

                # Read content (materializes the stream)
                content = response.content
                size_mb = len(content) / (1024 * 1024)
                self._log(f"Downloaded {size_mb:.2f} MB")

                # Create new response with content
                response._content = content
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e

                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(
                        f"Download attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)

        # All retries failed
        raise RuntimeError(
            f"Download failed after {self.MAX_RETRIES} attempts: {last_exception}"
        )

    def _check_cache(self) -> Optional[Any]:
        """
        Check if data exists in cache.

        Override this method in subclasses to implement caching logic.
        Return cached data if available, None otherwise.

        Returns:
            Cached data if available, None otherwise
        """
        return None

    def _save_to_cache(self, data: Any) -> None:
        """
        Save data to cache.

        Override this method in subclasses to implement caching logic.

        Args:
            data: Data to cache
        """
        pass

    def _log(self, message: str) -> None:
        """
        Log message if verbose mode enabled.

        Args:
            message: Message to log
        """
        if self.verbose:
            self.logger.info(message)
