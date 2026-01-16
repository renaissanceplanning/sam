# SAM BaseDownloader Architecture

## Overview

Instead of maintaining separate download modules, create a **unified downloader architecture** with:
- **BaseDownloader** abstract class with common functionality
- **Specialized downloaders** for different data source types
- **Module-specific downloaders** that inherit and customize

This approach eliminates the need for a separate `sam/download/` directory while providing:
- ✅ Consistent error handling
- ✅ Built-in progress tracking
- ✅ Unified caching
- ✅ Type-safe interfaces
- ✅ Easy extensibility

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│  BaseDownloader (abstract)                          │
│  - Common parameters (geoid, year, output_path)     │
│  - Workflow orchestration (download method)         │
│  - Progress tracking, logging, caching             │
└─────────────────────────────────────────────────────┘
                        ▲
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────┴────────┐              ┌───────┴────────┐
│ HTTPDownloader │              │ GeoDataDownloader│
│ (simple files) │              │ (GIS data)       │
└───────▲────────┘              └───────▲──────────┘
        │                               │
        │                               │
┌───────┴────────┐              ┌───────┴──────────┐
│ ZipDownloader  │              │ RasterDownloader │
│ (ZIP archives) │              │ (imagery/raster) │
└────────────────┘              └──────────────────┘
        ▲                               ▲
        │                               │
        │                               │
┌───────┴────────────┐          ┌───────┴──────────┐
│ Module-Specific    │          │ Module-Specific  │
│ (SLD, MS Buildings)│          │ (NLCD)          │
└────────────────────┘          └──────────────────┘
```

---

## Core Implementation

### 1. BaseDownloader (sam/core/downloader.py)

```python
"""
Base downloader class for all SAM data sources.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Union, Dict
import logging
import requests
from io import BytesIO

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
    - _validate_parameters()
    - _build_url()
    - _process_response()
    """

    # Class-level configuration (override in subclasses)
    DATA_SOURCE = "Unknown"
    REQUIRES_AUTH = False
    DEFAULT_CRS = "EPSG:4326"
    TIMEOUT = 60
    MAX_RETRIES = 3

    def __init__(
        self,
        geoid: Optional[Union[str, list]] = None,
        year: Optional[int] = None,
        output_path: Optional[Union[str, Path]] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        **kwargs
    ):
        """
        Initialize downloader.

        Args:
            geoid: Geographic identifier (FIPS code)
            year: Data year
            output_path: Where to save output (if applicable)
            cache_dir: Cache directory for downloaded files
            **kwargs: Module-specific parameters
        """
        self.geoid = geoid
        self.year = year
        self.output_path = Path(output_path) if output_path else None
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.kwargs = kwargs

        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def download(self) -> Any:
        """
        Execute full download workflow.

        Returns:
            Varies by subclass (GeoDataFrame, DataFrame, Path, etc.)

        Raises:
            ValueError: Invalid parameters
            RuntimeError: Download or processing failed
        """
        self.logger.info(f"Starting {self.DATA_SOURCE} download...")

        # 1. Validate parameters
        self._validate_parameters()

        # 2. Check cache (if enabled)
        if self.cache_dir:
            cached = self._check_cache()
            if cached is not None:
                self.logger.info("Loaded from cache")
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

        self.logger.info(f"{self.DATA_SOURCE} download complete")
        return result

    @abstractmethod
    def _validate_parameters(self) -> None:
        """
        Validate input parameters.

        Raises:
            ValueError: If parameters are invalid
        """
        pass

    @abstractmethod
    def _build_url(self) -> str:
        """
        Build download URL from parameters.

        Returns:
            Complete download URL
        """
        pass

    @abstractmethod
    def _process_response(self, response: requests.Response) -> Any:
        """
        Process HTTP response into final format.

        Args:
            response: requests.Response object

        Returns:
            Processed data (format varies by subclass)
        """
        pass

    def _download(self, url: str) -> requests.Response:
        """
        Download from URL with retry logic.

        Args:
            url: URL to download

        Returns:
            requests.Response object

        Raises:
            RuntimeError: If download fails after retries
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.info(f"Downloading from {url} (attempt {attempt + 1}/{self.MAX_RETRIES})")

                response = requests.get(
                    url,
                    stream=True,
                    timeout=self.TIMEOUT
                )
                response.raise_for_status()

                # Log download size
                size = len(response.content) / (1024 * 1024)  # MB
                self.logger.info(f"Downloaded {size:.2f} MB")

                return response

            except requests.exceptions.RequestException as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise RuntimeError(
                        f"Download failed after {self.MAX_RETRIES} attempts: {e}"
                    )
                self.logger.warning(f"Download attempt {attempt + 1} failed, retrying...")

    def _check_cache(self) -> Optional[Any]:
        """Check if data exists in cache."""
        # Implement caching logic (subclass can override)
        return None

    def _save_to_cache(self, data: Any) -> None:
        """Save data to cache."""
        # Implement caching logic (subclass can override)
        pass
```

### 2. Specialized Downloaders

```python
# sam/core/downloaders/http.py

class HTTPDownloader(BaseDownloader):
    """Downloads simple files via HTTP."""

    def _process_response(self, response: requests.Response) -> Union[bytes, Path]:
        """
        Save file to output_path or return bytes.

        Returns:
            Path if output_path specified, otherwise bytes
        """
        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'wb') as f:
                f.write(response.content)
            self.logger.info(f"Saved to {self.output_path}")
            return self.output_path
        return response.content


# sam/core/downloaders/zip.py

from zipfile import ZipFile

class ZipDownloader(BaseDownloader):
    """Downloads and processes ZIP archives."""

    @abstractmethod
    def _extract_from_zip(self, zf: ZipFile) -> Any:
        """
        Extract and process files from ZIP archive.

        Args:
            zf: ZipFile object

        Returns:
            Processed data (format varies by subclass)
        """
        pass

    def _process_response(self, response: requests.Response) -> Any:
        """Extract ZIP archive in-memory."""
        with ZipFile(BytesIO(response.content)) as zf:
            self.logger.debug(f"ZIP contains: {zf.namelist()}")
            return self._extract_from_zip(zf)


# sam/core/downloaders/geodata.py

import geopandas as gpd

class GeoDataDownloader(BaseDownloader):
    """Downloads GIS data, returns GeoDataFrame."""

    def _process_response(self, response: requests.Response) -> gpd.GeoDataFrame:
        """
        Parse response into GeoDataFrame.

        Override this method to handle different formats.
        """
        # Default: assume GeoJSON
        return gpd.read_file(BytesIO(response.content))


# sam/core/downloaders/raster.py

import rasterio

class RasterDownloader(BaseDownloader):
    """Downloads raster data, saves to file."""

    def _validate_parameters(self) -> None:
        """Rasters require output_path."""
        if not self.output_path:
            raise ValueError("output_path is required for raster downloads")

    def _process_response(self, response: requests.Response) -> Path:
        """Save raster to disk."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, 'wb') as f:
            f.write(response.content)

        self.logger.info(f"Saved raster to {self.output_path}")
        return self.output_path
```

### 3. Module-Specific Implementation Example

```python
# sam/nlcd/download.py

from sam.core.downloaders.raster import RasterDownloader
from typing import Literal

NLCD_YEARS = [2021, 2019, 2016, 2013, 2011, 2008, 2006, 2004, 2001]

NLCD_DATASETS = {
    'land_cover': 'Land_Cover',
    'impervious': 'Impervious',
    'impervious_descriptor': 'Impervious_descriptor',
    'tree_canopy': 'Tree_Canopy'
}


class NLCDDownloader(RasterDownloader):
    """
    Download NLCD raster data from MRLC S3 bucket.

    Examples:
        >>> downloader = NLCDDownloader(
        ...     geoid=['37183'],
        ...     year=2021,
        ...     dataset='land_cover',
        ...     output_path='nlcd_2021.tif'
        ... )
        >>> path = downloader.download()
    """

    DATA_SOURCE = "NLCD"
    BASE_URL = "https://s3-us-west-2.amazonaws.com/mrlc"

    def __init__(
        self,
        geoid: list,
        year: int,
        dataset: Literal['land_cover', 'impervious', 'impervious_descriptor', 'tree_canopy'] = 'land_cover',
        output_path: Path = None,
        region: str = 'conus',
        **kwargs
    ):
        super().__init__(geoid=geoid, year=year, output_path=output_path, **kwargs)
        self.dataset = dataset
        self.region = region

    def _validate_parameters(self) -> None:
        """Validate NLCD-specific parameters."""
        super()._validate_parameters()  # Check output_path exists

        if self.dataset not in NLCD_DATASETS:
            raise ValueError(
                f"Invalid dataset '{self.dataset}'. "
                f"Valid options: {list(NLCD_DATASETS.keys())}"
            )

        # Find closest year if exact match not available
        self.nlcd_year = min(NLCD_YEARS, key=lambda y: abs(y - self.year))
        if self.nlcd_year != self.year:
            self.logger.info(
                f"NLCD {self.year} not available, using {self.nlcd_year}"
            )

    def _build_url(self) -> str:
        """Build NLCD S3 URL."""
        dataset_name = NLCD_DATASETS[self.dataset]
        region_code = 'l48' if self.region == 'conus' else self.region

        # Release dates vary by year
        release_dates = {
            2021: '20230630',
            2019: '20210604',
            2016: '20210604',
            # ... etc
        }
        release_date = release_dates.get(self.nlcd_year, '20210604')

        filename = f"nlcd_{self.nlcd_year}_{self.dataset}_{region_code}_{release_date}.zip"
        return f"{self.BASE_URL}/{filename}"


# Public API function (backward compatible)
def download_nlcd(
    geoid: list,
    year: int,
    dataset: str = 'land_cover',
    output_path: Path = None,
    **kwargs
) -> Path:
    """
    Download NLCD raster data.

    Args:
        geoid: List of county FIPS codes
        year: Target year
        dataset: NLCD dataset type
        output_path: Where to save the file

    Returns:
        Path to downloaded raster file

    Examples:
        >>> path = download_nlcd(['37183'], 2021, 'land_cover', 'nlcd.tif')
    """
    downloader = NLCDDownloader(
        geoid=geoid,
        year=year,
        dataset=dataset,
        output_path=output_path,
        **kwargs
    )
    return downloader.download()
```

---

## Module Organization with BaseDownloader

### New Structure (Consolidated)

```
sam/
├── core/                       # NEW: Core infrastructure
│   ├── __init__.py
│   ├── downloader.py          # BaseDownloader
│   └── downloaders/           # Specialized downloaders
│       ├── __init__.py
│       ├── http.py            # HTTPDownloader
│       ├── zip.py             # ZipDownloader
│       ├── geodata.py         # GeoDataDownloader
│       └── raster.py          # RasterDownloader
│
├── nlcd/
│   ├── __init__.py
│   ├── core.py                # NLCD analysis class
│   └── download.py            # NLCDDownloader (extends RasterDownloader)
│
├── osm/
│   ├── __init__.py
│   ├── core.py                # OSMNetwork class
│   └── download.py            # OSMDownloader (extends GeoDataDownloader)
│
├── sld/
│   ├── __init__.py
│   └── download.py            # SLDDownloader (extends ZipDownloader)
│
├── parcels/
│   ├── __init__.py
│   ├── core.py                # High-level parcel API
│   └── download.py            # ParcelDownloader (extends HTTPDownloader)
│
└── ms_footprints/
    ├── __init__.py
    └── download.py            # MSFootprintsDownloader (extends GeoDataDownloader)
```

**Benefits:**
- ✅ No separate `download/` directory
- ✅ Consistent downloader pattern across modules
- ✅ Easy to add new data sources
- ✅ Built-in error handling, logging, caching
- ✅ Type-safe with clear interfaces

---

## Migration Strategy

### Phase 1: Create Core Infrastructure

1. Create `sam/core/` directory
2. Implement `BaseDownloader` in `sam/core/downloader.py`
3. Implement specialized downloaders in `sam/core/downloaders/`
4. Add comprehensive tests

### Phase 2: Refactor One Module (Proof of Concept)

Start with **NLCD** (good candidate because it's self-contained):

1. Create `sam/nlcd/download.py` with `NLCDDownloader` class
2. Maintain `download_nlcd()` function for backward compatibility
3. Update tests
4. Verify functionality

### Phase 3: Refactor Remaining Modules

Systematic conversion:
- MS Footprints → `MSFootprintsDownloader(GeoDataDownloader)`
- SLD → `SLDDownloader(ZipDownloader)`
- OSM → `OSMDownloader(GeoDataDownloader)`
- Parcels → `ParcelDownloader(HTTPDownloader)`

### Phase 4: Eliminate download/ Directory

Once all modules converted:
1. Delete `sam/download/` directory
2. Update all imports
3. Update documentation

---

## Example: Complete Module After Refactoring

```python
# sam/ms_footprints/__init__.py
"""
Microsoft Building Footprints module.

Provides access to building footprint data from Microsoft's open dataset.
"""

from .download import download_ms_footprints, MSFootprintsDownloader

__all__ = ['download_ms_footprints', 'MSFootprintsDownloader']


# sam/ms_footprints/download.py
from sam.core.downloaders.geodata import GeoDataDownloader
import geopandas as gpd
from io import BytesIO


class MSFootprintsDownloader(GeoDataDownloader):
    """Download Microsoft building footprints."""

    DATA_SOURCE = "Microsoft Building Footprints"
    BASE_URL = "https://usbuildingdata.blob.core.windows.net/usbuildings-v2"

    def __init__(self, state: str, **kwargs):
        super().__init__(**kwargs)
        self.state = state

    def _validate_parameters(self) -> None:
        if not isinstance(self.state, str):
            raise TypeError("state must be str")
        # Normalize state name
        self.state = self.state.upper()

    def _build_url(self) -> str:
        return f"{self.BASE_URL}/{self.state}.geojson.zip"

    def _process_response(self, response) -> gpd.GeoDataFrame:
        # Read GeoJSON from ZIP
        return gpd.read_file(
            BytesIO(response.content),
            **self.kwargs
        )


def download_ms_footprints(state: str, **kwargs) -> gpd.GeoDataFrame:
    """
    Download Microsoft building footprints for a state.

    Args:
        state: State abbreviation (e.g., 'NC', 'FL')
        **kwargs: Additional arguments passed to geopandas.read_file()

    Returns:
        GeoDataFrame with building footprints

    Examples:
        >>> gdf = download_ms_footprints('NC')
        >>> gdf = download_ms_footprints('FL', rows=1000)  # Limit rows
    """
    downloader = MSFootprintsDownloader(state=state, **kwargs)
    return downloader.download()
```

---

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Structure** | Scattered across download/ + top-level | Unified in each module |
| **Error handling** | Inconsistent | Standardized via BaseDownloader |
| **Caching** | Not implemented | Built into BaseDownloader |
| **Progress tracking** | Varies by module | Consistent logging |
| **Type safety** | Minimal type hints | Full type annotations |
| **Extensibility** | Copy-paste new downloaders | Inherit from base classes |
| **Testing** | Test each module separately | Test base class + specifics |
| **Documentation** | Scattered | Centralized in base class |

---

## Conclusion

The BaseDownloader architecture provides:

1. **Simplified structure**: No separate download/ directory needed
2. **Consistency**: All downloaders follow same pattern
3. **Maintainability**: Common functionality in base classes
4. **Extensibility**: Easy to add new data sources
5. **Better UX**: Built-in progress tracking, caching, error handling

This approach is **superior to the current download/ directory** because:
- Eliminates duplication between `sam/X/` and `sam/download/X/`
- Provides clear inheritance hierarchy
- Makes it obvious where new download code belongs
- Reduces cognitive load (one pattern to learn)

**Recommendation**: Implement BaseDownloader architecture as part of the overall simplification plan.
