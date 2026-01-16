"""
Raster downloader for imagery and raster data.
"""

from pathlib import Path
import requests

from sam.core.downloader import BaseDownloader


class RasterDownloader(BaseDownloader):
    """
    Downloads raster data and saves to file.

    Raster downloads require output_path to be specified since raster
    data is too large to keep in memory and must be saved to disk.

    Attributes:
        SUPPORTED_FORMATS (list): Raster formats this downloader supports

    Examples:
        >>> class NLCDDownloader(RasterDownloader):
        ...     def _validate_parameters(self):
        ...         super()._validate_parameters()  # Checks output_path
        ...         if not self.year:
        ...             raise ValueError("year is required")
        ...
        ...     def _build_url(self):
        ...         return f"https://example.com/nlcd_{self.year}.tif"
        ...
        >>> downloader = NLCDDownloader(year=2021, output_path='nlcd.tif')
        >>> path = downloader.download()
        >>> print(path)
        PosixPath('nlcd.tif')
    """

    SUPPORTED_FORMATS = ['tif', 'tiff', 'img', 'grd', 'nc']

    def _validate_parameters(self) -> None:
        """
        Raster downloads require output_path.

        Raises:
            ValueError: If output_path is not specified
        """
        if not self.output_path:
            raise ValueError(
                f"{self.DATA_SOURCE} downloads require output_path to be specified. "
                "Raster data is too large to return in memory."
            )

    def _process_response(self, response: requests.Response) -> Path:
        """
        Save raster to disk and return file path.

        Args:
            response: HTTP response with raster data

        Returns:
            Path to saved raster file

        Examples:
            >>> def _process_response(self, response):
            ...     # Save raw response
            ...     super()._process_response(response)
            ...     # Optionally post-process with rasterio
            ...     return self.output_path
        """
        self._log(f"Saving raster to {self.output_path}...")

        # Create parent directory if needed
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save raster data
        with open(self.output_path, 'wb') as f:
            f.write(response.content)

        # Log file size
        size_mb = self.output_path.stat().st_size / (1024 * 1024)
        self._log(f"Saved {size_mb:.2f} MB raster to {self.output_path}")

        return self.output_path
