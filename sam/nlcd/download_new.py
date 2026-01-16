"""
NLCD downloader using BaseDownloader architecture.

This is the NEW implementation that will replace sam/download/nlcd/core.py
"""

from pathlib import Path
from typing import Literal, Optional
import geopandas as gpd

from sam.core.downloaders.raster import RasterDownloader
from sam.config import COUNTIES as county_shapes

# Available NLCD years (as of 2024)
NLCD_YEARS = [2021, 2019, 2016, 2013, 2011, 2008, 2006, 2004, 2001]

# NLCD dataset types
NLCD_DATASETS = {
    'land_cover': 'Land_Cover',
    'impervious': 'Impervious',
    'impervious_descriptor': 'Impervious_descriptor',
    'tree_canopy': 'Tree_Canopy'
}

# Release dates for NLCD products
RELEASE_DATES = {
    2021: '20230630',
    2019: '20210604',
    2016: '20210604',
    2013: '20210604',
    2011: '20210604',
    2008: '20210604',
    2006: '20210604',
    2004: '20210604',
    2001: '20210604'
}


def get_closest_nlcd_year(target_year: int) -> int:
    """
    Find the closest available NLCD year to the target year.

    Args:
        target_year: The desired year

    Returns:
        The closest available NLCD year

    Examples:
        >>> get_closest_nlcd_year(2020)
        2019
        >>> get_closest_nlcd_year(2024)
        2021
    """
    return min(NLCD_YEARS, key=lambda year: abs(year - target_year))


class NLCDDownloader(RasterDownloader):
    """
    Download NLCD raster data from MRLC S3 bucket.

    Inherits from RasterDownloader which provides:
    - Automatic retry logic
    - Progress tracking
    - File saving
    - Error handling

    Attributes:
        DATA_SOURCE: "NLCD" (for logging)
        BASE_URL: S3 bucket base URL

    Examples:
        >>> downloader = NLCDDownloader(
        ...     geoid=['37183'],
        ...     year=2021,
        ...     dataset='land_cover',
        ...     output_path='nlcd_2021.tif',
        ...     region='conus'
        ... )
        >>> path = downloader.download()
        >>> print(path)
        PosixPath('nlcd_2021.tif')

        >>> # With auto year selection
        >>> downloader = NLCDDownloader(
        ...     geoid=['37183'],
        ...     year=2024,  # Will use 2021 (closest)
        ...     dataset='impervious',
        ...     output_path='nlcd_impervious.tif'
        ... )
        >>> path = downloader.download()
        # Logs: "NLCD 2024 not available, using 2021"
    """

    DATA_SOURCE = "NLCD"
    BASE_URL = "https://s3-us-west-2.amazonaws.com/mrlc"

    def __init__(
        self,
        geoid: list,
        year: int,
        dataset: Literal['land_cover', 'impervious', 'impervious_descriptor', 'tree_canopy'] = 'land_cover',
        output_path: Optional[Path] = None,
        region: Literal['conus', 'alaska', 'hawaii', 'puerto_rico'] = 'conus',
        clip_to_aoi: bool = False,
        **kwargs
    ):
        """
        Initialize NLCD downloader.

        Args:
            geoid: List of county FIPS codes (used for clipping if enabled)
            year: Target year (will use closest available)
            dataset: NLCD dataset type
            output_path: Where to save the raster file
            region: Geographic region
            clip_to_aoi: If True, clip raster to geoid boundaries (requires rasterio)
            **kwargs: Additional arguments
        """
        super().__init__(geoid=geoid, year=year, output_path=output_path, **kwargs)
        self.dataset = dataset
        self.region = region
        self.clip_to_aoi = clip_to_aoi
        self.nlcd_year = None  # Will be set in _validate_parameters

    def _validate_parameters(self) -> None:
        """
        Validate NLCD-specific parameters.

        Raises:
            ValueError: If dataset or region is invalid
        """
        # Check output_path (required for rasters)
        super()._validate_parameters()

        # Validate dataset
        if self.dataset not in NLCD_DATASETS:
            raise ValueError(
                f"Invalid dataset '{self.dataset}'. "
                f"Valid options: {list(NLCD_DATASETS.keys())}"
            )

        # Validate region
        valid_regions = ['conus', 'alaska', 'hawaii', 'puerto_rico']
        if self.region not in valid_regions:
            raise ValueError(
                f"Invalid region '{self.region}'. "
                f"Valid options: {valid_regions}"
            )

        # Find closest year if exact match not available
        self.nlcd_year = get_closest_nlcd_year(self.year)
        if self.nlcd_year != self.year:
            self._log(
                f"NLCD {self.year} not available, using {self.nlcd_year}"
            )

    def _build_url(self) -> str:
        """
        Build NLCD S3 download URL.

        Returns:
            Complete S3 URL for NLCD ZIP file

        Examples:
            >>> # For 2021 land cover
            "https://s3-us-west-2.amazonaws.com/mrlc/nlcd_2021_land_cover_l48_20230630.zip"
        """
        # Map dataset to URL naming
        dataset_name = NLCD_DATASETS[self.dataset]

        # Map region to code
        region_codes = {
            'conus': 'l48',
            'alaska': 'ak',
            'hawaii': 'hi',
            'puerto_rico': 'pr'
        }
        region_code = region_codes[self.region]

        # Get release date
        release_date = RELEASE_DATES.get(self.nlcd_year, '20210604')

        # Build filename following NLCD naming convention
        # Format: nlcd_{year}_{dataset}_{region}_{release}.zip
        filename = f"nlcd_{self.nlcd_year}_{self.dataset}_{region_code}_{release_date}.zip"

        return f"{self.BASE_URL}/{filename}"

    def _process_response(self, response) -> Path:
        """
        Save raster and optionally clip to AOI.

        Args:
            response: HTTP response with NLCD ZIP file

        Returns:
            Path to saved (and optionally clipped) raster

        Notes:
            If clip_to_aoi=True, requires rasterio and extracts/clips the ZIP.
            Otherwise, saves ZIP file as-is.
        """
        if self.clip_to_aoi:
            return self._save_and_clip(response)
        else:
            # Save ZIP file directly
            return super()._process_response(response)

    def _save_and_clip(self, response) -> Path:
        """
        Extract ZIP, clip raster to geoid boundaries, and save.

        Args:
            response: HTTP response with NLCD ZIP file

        Returns:
            Path to clipped raster file

        Raises:
            ImportError: If rasterio not available
            ValueError: If no raster file found in ZIP
        """
        try:
            import rasterio
            from rasterio.mask import mask as rio_mask
            import zipfile
            from shapely import geometry
            from io import BytesIO

        except ImportError:
            raise ImportError(
                "clip_to_aoi=True requires rasterio. "
                "Install with: pip install rasterio"
            )

        self._log("Clipping raster to area of interest...")

        # Extract ZIP to find raster file
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            raster_files = [
                f for f in zip_ref.namelist()
                if f.endswith(('.tif', '.img'))
            ]

            if not raster_files:
                raise ValueError("No raster file (.tif or .img) found in ZIP")

            # Extract to temp location
            temp_dir = self.output_path.parent / 'temp_nlcd'
            temp_dir.mkdir(exist_ok=True)
            zip_ref.extractall(temp_dir)
            raster_file = temp_dir / raster_files[0]

        # Get clipping geometry from geoids
        counties = county_shapes[county_shapes.GEOID.isin(self.geoid)]
        bounds = counties.total_bounds
        bbox_geom = geometry.box(bounds[0], bounds[1], bounds[2], bounds[3])
        bbox_gdf = gpd.GeoDataFrame({'geometry': [bbox_geom]}, crs=counties.crs)

        # Clip raster
        with rasterio.open(raster_file) as src:
            # Reproject bbox to match raster CRS
            bbox_reproj = bbox_gdf.to_crs(src.crs)

            # Clip
            out_image, out_transform = rio_mask(
                src,
                bbox_reproj.geometry,
                crop=True
            )

            # Update metadata
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })

            # Save clipped raster
            clipped_path = self.output_path.parent / f"{self.output_path.stem}_clipped.tif"
            with rasterio.open(clipped_path, "w", **out_meta) as dest:
                dest.write(out_image)

        # Clean up temp files
        import shutil
        shutil.rmtree(temp_dir)

        self._log(f"Clipped raster saved to: {clipped_path}")
        return clipped_path


def download_nlcd(
    geoid: list,
    year: int,
    dataset: str = 'land_cover',
    output_path: Optional[Path] = None,
    clip_to_aoi: bool = False,
    **kwargs
) -> Path:
    """
    Download NLCD raster data (backward compatible function).

    Args:
        geoid: List of county FIPS codes
        year: Target year (uses closest available)
        dataset: NLCD dataset type ('land_cover', 'impervious', etc.)
        output_path: Where to save the raster file
        clip_to_aoi: If True, clip raster to geoid boundaries
        **kwargs: Additional arguments

    Returns:
        Path to downloaded (and optionally clipped) raster file

    Examples:
        >>> # Basic download
        >>> path = download_nlcd(
        ...     geoid=['37183'],
        ...     year=2021,
        ...     dataset='land_cover',
        ...     output_path='nlcd.tif'
        ... )

        >>> # Download and clip
        >>> path = download_nlcd(
        ...     geoid=['37183', '37063'],
        ...     year=2019,
        ...     dataset='impervious',
        ...     output_path='nlcd_impervious.tif',
        ...     clip_to_aoi=True
        ... )
    """
    downloader = NLCDDownloader(
        geoid=geoid,
        year=year,
        dataset=dataset,
        output_path=output_path,
        clip_to_aoi=clip_to_aoi,
        **kwargs
    )
    return downloader.download()
