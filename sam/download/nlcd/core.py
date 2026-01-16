# -*- coding: utf-8 -*-
"""
Updated NLCD downloader that works with current MRLC website structure.

The MRLC website changed their data structure, so this provides a simplified
approach that downloads NLCD data directly from known URLs.
"""

import geopandas as gpd
from shapely import geometry
from typing import Literal, Optional
import requests
from pathlib import Path

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
    
    The MRLC changed their website structure, but data is still available
    via direct URLs following a predictable pattern.
    
    Args:
        year: NLCD year (will use closest available if exact year not available)
        dataset: Type of NLCD data
        region: Geographic region
        
    Returns:
        Direct download URL for the NLCD GeoTIFF
        
    Examples:
        >>> build_nlcd_url(2021, 'land_cover', 'conus')
        'https://s3-us-west-2.amazonaws.com/mrlc/nlcd_2021_land_cover_l48_20230630.zip'
    """
    # Get closest available year
    nlcd_year = get_closest_nlcd_year(year)
    
    # Base URL for MRLC S3 bucket
    base_url = "https://s3-us-west-2.amazonaws.com/mrlc"
    
    # Dataset naming in URLs
    dataset_name = NLCD_DATASETS.get(dataset, 'Land_Cover')
    
    # Region codes
    region_codes = {
        'conus': 'l48',
        'alaska': 'ak',
        'hawaii': 'hi', 
        'puerto_rico': 'pr'
    }
    region_code = region_codes.get(region, 'l48')
    
    # Build URL based on common NLCD naming patterns
    # Format: nlcd_{year}_{dataset}_{region}_{release_date}.zip
    # Release dates vary by year - using known patterns
    release_dates = {
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
    
    release_date = release_dates.get(nlcd_year, '20210604')
    
    # Construct filename
    filename = f"nlcd_{nlcd_year}_{dataset}_{region_code}_{release_date}.zip"
    
    return f"{base_url}/{filename}"


def download_nlcd(
    geoid: list[str],
    year: int,
    dataset: Literal['land_cover', 'impervious', 'impervious_descriptor', 'tree_canopy'] = 'land_cover',
    output_path: Optional[Path] = None,
    clip_to_aoi: bool = False,
    summary_areas: Optional[gpd.GeoDataFrame] = None
) -> Path:
    """
    Download NLCD data for specified counties.
    
    Args:
        geoid: List of 5-digit GEOID codes (state + county FIPS)
        year: Desired year (will use closest available)
        dataset: Type of NLCD data to download
        output_path: Where to save the downloaded file (optional)
        clip_to_aoi: If True, clips the raster to the bounding box of the geoids
            after download. Requires rasterio. Default: False (downloads full tile)
        summary_areas: Optional GeoDataFrame to use for clipping instead of geoid bounds
        
    Returns:
        Path to the downloaded/clipped file
        
    Examples:
        >>> # Download full CONUS tile
        >>> path = download_nlcd(['37183'], 2021, 'land_cover')
        
        >>> # Download and clip to counties
        >>> path = download_nlcd(['37183'], 2021, 'land_cover', clip_to_aoi=True)
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
        print(f"Error downloading NLCD data: {e}")
        print(f"URL attempted: {url}")
        print(f"\nThe URL structure may have changed. Try visiting:")
        print(f"https://www.mrlc.gov/data to find current download links")
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
    print(f"2020 → {get_closest_nlcd_year(2020)}")  # Should return 2019
    print(f"2024 → {get_closest_nlcd_year(2024)}")  # Should return 2021
    print(f"2013 → {get_closest_nlcd_year(2013)}")  # Should return 2013
    
    # Test URL building
    print("\nTesting build_nlcd_url:")
    url = build_nlcd_url(2021, 'land_cover', 'conus')
    print(f"2021 Land Cover CONUS: {url}")
    
    # Test download (commented out - uncomment to actually download)
    # print("\nTesting download:")
    # geoids = ['37183']  # Wake County, NC
    # path = download_nlcd(geoids, 2021, 'land_cover', Path('test_nlcd.zip'))