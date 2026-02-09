# -*- coding: utf-8 -*-
"""
Updated NLCD downloader that works with current MRLC website structure.

The MRLC website changed their data structure, so this provides a simplified
approach that downloads NLCD data directly from known URLs.
"""

import geopandas as gpd
from shapely import geometry
from typing import Literal, Optional, Union
import requests
from pathlib import Path

from sam.config import COUNTIES as county_shapes

# Available NLCD years (as of 2026)
# Note: Annual NLCD products now available starting from 1985
# Legacy NLCD products: 2021, 2019, 2016, 2013, 2011, 2008, 2006, 2004, 2001
# Annual NLCD: 2024, 2023, 2022, 2021, 2020, 2019, ..., 1985
NLCD_YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2016, 2013, 2011, 2008, 2006, 2004, 2001]

# NLCD dataset types - maps user-friendly names to URL codes
NLCD_DATASETS = {
    'land_cover': 'LndCov',           # Land Cover (annual, 1985-2024)
    'impervious': 'FctImp',           # Fractional Impervious Surface (annual, 1985-2024)
    'impervious_descriptor': None,    # Not available in Annual NLCD yet
    'tree_canopy': 'TCC'              # Tree Canopy Cover (annual, 1985-2023, USFS product)
}

# Tree Canopy Cover info
TREE_CANOPY_YEARS = list(range(1985, 2024))  # Annual data 1985-2023
TREE_CANOPY_VERSION = "v2023-5"  # Current USFS version (released 2025)


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


def build_nlcd_url(
    year: int,
    dataset: Literal['land_cover', 'impervious', 'impervious_descriptor', 'tree_canopy'] = 'land_cover',
    region: Literal['conus', 'alaska', 'hawaii', 'puerto_rico'] = 'conus'
) -> str:
    """
    Build the direct download URL for NLCD data.

    MRLC changed their URLs in 2024/2025. The S3 bucket is now blocked (403 Forbidden).
    New URLs use the pattern: https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/

    Args:
        year: NLCD year (will use closest available if exact year not available)
        dataset: Type of NLCD data
        region: Geographic region

    Returns:
        Direct download URL for the NLCD data

    Examples:
        >>> build_nlcd_url(2024, 'land_cover', 'conus')
        'https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2024_CU_C1V1.zip'
    """
    # Get closest available year
    nlcd_year = get_closest_nlcd_year(year)

    # New base URL (as of 2025)
    # Old S3 bucket (s3-us-west-2.amazonaws.com/mrlc) returns 403 Forbidden
    base_url = "https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles"

    # For years 2019+, use Annual NLCD products
    # These are updated annually and available through the new portal
    if nlcd_year >= 2019:
        # Annual NLCD format: Annual_NLCD_LndCov_{year}_CU_C1V1.zip
        # CU = CONUS (Continental US)
        # C1V1 = Collection 1, Version 1

        # Region codes for Annual NLCD
        region_codes = {
            'conus': 'CU',
            'alaska': 'AK',
            'hawaii': 'HI',
            'puerto_rico': 'PR'
        }
        region_code = region_codes.get(region, 'CU')

        # Get the product code from NLCD_DATASETS
        product_code = NLCD_DATASETS.get(dataset)

        # Tree Canopy Cover uses a different URL structure (USFS)
        if dataset == 'tree_canopy' and product_code == 'TCC':
            # Tree Canopy Cover is from USDA Forest Service, not MRLC bundles
            # URL pattern: https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/docs/v2023-5/nlcd_tcc_CONUS_2023_v2023-5_wgs84.zip
            usfs_base = "https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/docs"

            # Region codes for USFS (different from MRLC)
            usfs_region_codes = {
                'conus': 'CONUS',
                'alaska': 'SEAK',  # Southeast Alaska
                'hawaii': 'HAWAII',
                'puerto_rico': 'PRUSVI'  # Puerto Rico + US Virgin Islands
            }
            usfs_region = usfs_region_codes.get(region, 'CONUS')

            # Check if year is available for TCC (1985-2023)
            if nlcd_year < 1985 or nlcd_year > 2023:
                print(f"Warning: Tree Canopy Cover only available for 1985-2023")
                print(f"Requested year {nlcd_year} not available, using 2023")
                nlcd_year = 2023

            filename = f"nlcd_tcc_{usfs_region}_{nlcd_year}_{TREE_CANOPY_VERSION}_wgs84.zip"
            return f"{usfs_base}/{TREE_CANOPY_VERSION}/{filename}"

        elif product_code is None:
            # Dataset not available in Annual NLCD
            print(f"Warning: {dataset} not yet available in Annual NLCD")
            print(f"Falling back to land_cover")
            product_code = 'LndCov'

        # Construct filename: Annual_NLCD_{product}_{year}_{region}_C1V1.zip
        filename = f"Annual_NLCD_{product_code}_{nlcd_year}_{region_code}_C1V1.zip"

        return f"{base_url}/{filename}"

    else:
        # For older years (2016 and earlier), try legacy NLCD products
        # These may still be on the old S3 bucket or require manual download
        print(f"Warning: NLCD {nlcd_year} is a legacy product")
        print(f"The old S3 bucket URLs no longer work (403 Forbidden)")
        print(f"Please download manually from https://www.mrlc.gov/data")

        # Return a placeholder URL that will fail with helpful error message
        # This triggers the exception handler below which provides manual download instructions
        return f"{base_url}/LEGACY_PRODUCT_REQUIRES_MANUAL_DOWNLOAD_{nlcd_year}.zip"


def download_nlcd(
    geoid: list[str],
    year: int,
    dataset: Literal['land_cover', 'impervious', 'impervious_descriptor', 'tree_canopy'] = 'land_cover',
    output_path: Optional[Path] = None,
    clip_to_aoi: bool = False,
    summary_areas: Optional[gpd.GeoDataFrame] = None
) -> Union[Path, dict[str, Path]]:
    """
    Download NLCD data for specified counties.

    **Available Products (as of 2025):**
    - **land_cover**: Land Cover classes (annual, 1985-2024) ✓
    - **impervious**: Fractional Impervious Surface (annual, 1985-2024) ✓
    - **tree_canopy**: Tree Canopy Cover (annual, 1985-2023, USFS) ✓
    - **impervious_descriptor**: Not yet available in Annual NLCD ✗

    Args:
        geoid: List of 5-digit GEOID codes (state + county FIPS)
        year: Desired year (will use closest available)
        dataset: Type of NLCD data to download:
            - 'land_cover': Land cover classes (default)
            - 'impervious': Fractional impervious surface (0-100%)
            - 'tree_canopy': Tree canopy cover (separate product, see notes)
            - 'impervious_descriptor': Not available yet
        output_path: Where to save the downloaded file (optional)
        clip_to_aoi: If True, clips the raster to the bounding box of the geoids
            after download. Requires rasterio. Default: False (downloads full tile)
        summary_areas: Optional GeoDataFrame to use for clipping instead of geoid bounds

    Returns:
        Path to the downloaded/clipped file

    Notes:
        - Tree Canopy Cover (annual 1985-2023) from USDA Forest Service v2023-5
        - Tree Canopy is ~3.6 GB per year (larger than other NLCD products)
        - Impervious Descriptor not yet available in Annual NLCD products
        - All products use WGS84 (EPSG:4326) coordinate system
        - When clip_to_aoi=True: Original zip files are deleted after clipping to save disk space

    Examples:
        >>> # Download land cover
        >>> path = download_nlcd(['12057'], 2024, 'land_cover')

        >>> # Download fractional impervious surface
        >>> path = download_nlcd(['12057'], 2024, 'impervious')

        >>> # Download and clip to county boundary
        >>> path = download_nlcd(['12057'], 2024, 'land_cover', clip_to_aoi=True)
    """
    from sam.config import COUNTIES as county_shapes
    
    # Determine region from first geoid
    state_fips = geoid[0][:2]
    
    # Map state FIPS to region
    if state_fips == '02':  # Alaska
        region = 'alaska'
    elif state_fips == '15':  # Hawaii
        region = 'hawaii'
    elif state_fips == '72':  # Puerto Rico
        region = 'puerto_rico'
    else:
        region = 'conus'
    
    # Get the closest available year
    nlcd_year = get_closest_nlcd_year(year)
    
    if nlcd_year != year:
        print(f"Note: NLCD {year} not available, using {nlcd_year} instead")
    
    # Build download URL
    url = build_nlcd_url(nlcd_year, dataset, region)
    
    # Set output path for downloaded zip
    if output_path is None:
        output_path = Path(f"nlcd_{nlcd_year}_{dataset}_{region}.zip")
    else:
        output_path = Path(output_path)
    
    # Download the file
    print(f"Downloading NLCD {nlcd_year} {dataset} from {url}")
    print(f"This may take a while - NLCD files are large (typically 1-5 GB)")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Download with progress indication
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='')
        
        print(f"\nDownload complete: {output_path}")
        
        # Clip if requested
        if clip_to_aoi:
            print("\nClipping raster to area of interest...")
            try:
                import rasterio
                from rasterio.mask import mask as rio_mask
                import zipfile
                
                # Extract the zip to find the .tif or .img file
                with zipfile.ZipFile(output_path, 'r') as zip_ref:
                    # Find the raster file
                    raster_files = [f for f in zip_ref.namelist()
                                   if f.endswith(('.tif', '.img'))]
                    if not raster_files:
                        print("Warning: No raster file found in zip, skipping clip")
                        return output_path

                    # Extract to temp location
                    temp_dir = output_path.parent / 'temp_nlcd'
                    temp_dir.mkdir(exist_ok=True)
                    zip_ref.extractall(temp_dir)
                    raster_file = temp_dir / raster_files[0]
                
                # Get clipping geometry
                if summary_areas is not None:
                    clip_geom = summary_areas
                else:
                    # Use county boundaries
                    counties = county_shapes[county_shapes.GEOID.isin(geoid)]
                    clip_geom = counties
                
                # Create bounding box
                bounds = clip_geom.total_bounds
                bbox_geom = geometry.box(bounds[0], bounds[1], bounds[2], bounds[3])
                bbox_gdf = gpd.GeoDataFrame(
                    {'geometry': [bbox_geom]}, 
                    crs=clip_geom.crs
                )
                
                # Clip the raster
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
                    clipped_path = output_path.parent / f"{output_path.stem}_clipped.tif"
                    with rasterio.open(clipped_path, "w", **out_meta) as dest:
                        dest.write(out_image)

                    print(f"Clipped raster saved to: {clipped_path}")

                # Clean up temp files
                import shutil
                shutil.rmtree(temp_dir)

                # Delete the original zip file after successful clipping to save disk space
                try:
                    output_path.unlink()
                    print(f"Deleted original zip file: {output_path.name} (saved ~{total_size / (1024**3):.1f} GB)")
                except Exception as e:
                    print(f"Warning: Could not delete zip file {output_path}: {e}")

                return clipped_path
                
            except ImportError:
                print("Warning: rasterio not available, skipping clip")
                print("Install rasterio to enable automatic clipping: pip install rasterio")
                return output_path
            except Exception as e:
                print(f"Warning: Clipping failed: {e}")
                print("Returning full downloaded file")
                return output_path
        
        return output_path
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"Error 403 Forbidden: Access denied to NLCD data")
            print(f"URL attempted: {url}")
            print(f"\nThe old MRLC S3 bucket URLs no longer work (changed in 2024/2025).")
            print(f"SAM has been updated to use new MRLC URLs, but this year/dataset may not be available.")
            print(f"\nAlternative download methods:")
            print(f"1. Visit https://www.mrlc.gov/data to download manually")
            print(f"2. Try the MRLC Data Viewer: https://www.mrlc.gov/viewer/")
            print(f"3. Use the USGS National Map: https://apps.nationalmap.gov/downloader/")
            print(f"4. Use Annual NLCD (2019-2024): https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/")
            print(f"\nAfter manual download, save to: {output_path}")
        elif e.response.status_code == 404:
            print(f"Error 404 Not Found: NLCD data file not available")
            print(f"URL attempted: {url}")
            print(f"\nThis specific year/dataset combination may not be available.")
            print(f"Available years for Annual NLCD: 2019-2024")
            print(f"Available years for Legacy NLCD: 2021, 2019, 2016, 2013, 2011, 2008, 2006, 2004, 2001")
            print(f"\nTry visiting https://www.mrlc.gov/data to find available downloads")
        else:
            print(f"Error downloading NLCD data: {e}")
            print(f"URL attempted: {url}")
            print(f"\nTry visiting https://www.mrlc.gov/data to find current download links")
        raise


def get_nlcd_bbox(geoid: list[str]) -> gpd.GeoDataFrame:
    """
    Get bounding box for NLCD download based on county GEOIDs.
    
    Args:
        geoid: List of 5-digit GEOID codes
        
    Returns:
        GeoDataFrame with bounding box geometry
    """
    # Get counties
    counties = county_shapes[county_shapes.GEOID.isin(geoid)]
    
    # Get bounding box
    bounds = counties.total_bounds
    
    # Create bbox geodataframe
    bbox_dict = {
        "id": ["nlcd_bbox"],
        "geometry": [geometry.box(bounds[0], bounds[1], bounds[2], bounds[3])],
    }
    
    bbox = gpd.GeoDataFrame(bbox_dict, crs=counties.crs).to_crs("EPSG:4326")
    
    return bbox


# Example usage and testing
if __name__ == "__main__":
    # Test closest year function
    print("Testing get_closest_nlcd_year:")
    print(f"2025 → {get_closest_nlcd_year(2025)}")  # Should return 2024
    print(f"2020 → {get_closest_nlcd_year(2020)}")  # Should return 2020
    print(f"2013 → {get_closest_nlcd_year(2013)}")  # Should return 2013

    # Test URL building
    print("\nTesting build_nlcd_url (new URLs as of 2025):")
    url_2024 = build_nlcd_url(2024, 'land_cover', 'conus')
    print(f"2024 Land Cover CONUS: {url_2024}")

    url_2021 = build_nlcd_url(2021, 'land_cover', 'conus')
    print(f"2021 Land Cover CONUS: {url_2021}")

    url_2016 = build_nlcd_url(2016, 'land_cover', 'conus')
    print(f"2016 Land Cover CONUS (Legacy): {url_2016}")

    # Test download (commented out - uncomment to actually download)
    # print("\nTesting download:")
    # geoids = ['12057']  # Hillsborough County, FL
    # path = download_nlcd(geoids, 2024, 'land_cover', Path('test_nlcd.zip'))