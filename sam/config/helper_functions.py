from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

import geopandas as gpd
from sam.config import COUNTIES as county_shapes

logger = logging.getLogger(__name__)


def is_int(element):
    """
    Check if an element can be converted to an integer.

    This function attempts to convert the given 'element' to an integer.
    If the conversion is successful, it returns True; otherwise, it returns False.

    Args:
        element (str): The element to be checked for integer conversion.

    Returns:
        bool: True if the 'element' can be converted to an integer, False otherwise.

    Example:
        >>> is_int("123")
        True
        >>> is_int("abc")
        False
        >>> is_int("42.5")
        False
    """
    try:
        int(element)
        return True
    except ValueError:
        return False


def extract_fips(gdf):
    """Finds the county level fips and names for a given geometry

    Args:
        gdf (gpd.GeoDataFrame): A gdf containing summary area polygons

    Returns:
        tuple: A tuple containing strings for geoids and county names.
    """
    # Reproject to match county shapes CRS
    gdf = gdf.to_crs(county_shapes.crs)
    dissolved = gdf.dissolve().geometry[0]

    # Find all intersecting counties
    intersecting = county_shapes[county_shapes.intersects(dissolved)]

    if len(intersecting) == 1:
        # Only one county intersects - use it
        county = intersecting
    else:
        # Multiple counties intersect - use the one with largest overlap
        # Calculate intersection area for each county
        intersecting = intersecting.copy()
        intersecting['overlap_area'] = intersecting.geometry.intersection(dissolved).area
        # Sort by overlap area and take the largest
        county = intersecting.nlargest(1, 'overlap_area')

    geoids = county["GEOID"].unique().tolist()
    county_names = county["NAME"].unique().tolist()

    return geoids, county_names


def create_geo_dict(geoids):
    """
    Creates a dictionary mapping U.S. state codes to their associated county codes.

    Args:
        geoids (list): A list of geographic identifier codes, where each code
            consists of a 2-letter state code followed by a 3-digit county code.

    Returns:
        dict: A dictionary where the keys are state codes (e.g., 'NY' for New York)
            and the values are lists of county codes associated with that state.

    Example:
        >>> geoids = ['10003', '24015', '42029', '42015']
        >>> create_geo_dict(geoids)
        {'10': ['03'], '24': ['15'], '42': ['29', '15']}
    """
    states = set([st[0:2] for st in geoids])

    geo_dict = {
        state: [cnt[2:] for cnt in geoids if (cnt[0:2] == state)]
        for state in states    
        }
    
    return geo_dict


# =============================================================================
# Directory Management
# =============================================================================

def get_data_dir_paths(data_dir: Union[str, Path]) -> Dict[str, Path]:
    """
    Get dictionary of data directory paths WITHOUT creating them.
    
    This function returns a mapping of directory keys to their paths,
    but does not create any directories on the filesystem. Directories
    should be created explicitly when needed using ensure_dir_exists().

    Args:
        data_dir: Root directory path for data storage.

    Returns:
        Dictionary mapping directory keys to Path objects (not yet created).
        Available keys:
            - 'raw_dir': Main RAW data directory
            - 'lodes_dir': LODES employment data
            - 'acs_dir': American Community Survey data
            - 'shp_dir': TIGER/Line shapefiles
            - 'net_dir': OpenStreetMap network data
            - 'par_dir': Parcel data
            - 'lih_dir': Low Income Housing Tax Credit data
            - 'rep_dir': Replica data
            - 'nlcd_dir': National Land Cover Database
            - 'sld_dir': School district data

    Examples:
        >>> paths = get_data_dir_paths('/path/to/data')
        >>> print(paths['lodes_dir'])
        /path/to/data/RAW/lodes
        >>> # Note: Directory not created yet!
    """
    data_dir = Path(data_dir)
    
    return {
        'raw_dir': data_dir / "RAW",
        'lodes_dir': data_dir / "RAW" / "lodes",
        'acs_dir': data_dir / "RAW" / "acs",
        'shp_dir': data_dir / "RAW" / "tiger",
        'net_dir': data_dir / "RAW" / "osm",
        'par_dir': data_dir / "RAW" / "parcels",
        'lih_dir': data_dir / "RAW" / "lihtc",
        'rep_dir': data_dir / "RAW" / "replica",
        'nlcd_dir': data_dir / "RAW" / "nlcd",
        'sld_dir': data_dir / "RAW" / "sld"
    }


def ensure_dir_exists(path: Union[Path, str]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    This function creates the directory and any necessary parent directories.
    If the directory already exists, no action is taken.

    Args:
        path: Directory path to create.

    Returns:
        The path as a Path object (for chaining).

    Raises:
        OSError: If directory creation fails due to permissions or other OS errors.

    Examples:
        >>> data_path = ensure_dir_exists('/path/to/data/lodes')
        >>> print(data_path.exists())
        True
        >>> 
        >>> # Can be chained
        >>> csv_path = ensure_dir_exists(Path('/data/acs')) / 'output.csv'
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
    return path


def validate_data_dir(
    data_dir: Union[str, Path],
    required_dirs: Optional[List[str]] = None
) -> Dict[str, Path]:
    """
    Get data directory paths, optionally creating only specified directories.
    
    This function replaces the old validate_data_dir that created all directories
    upfront. Now you have explicit control over which directories are created.

    Args:
        data_dir: Root directory path for data storage.
        required_dirs: Optional list of directory keys to create immediately.
            If None (default), no directories are created upfront - they should
            be created explicitly when needed using ensure_dir_exists().
            Valid keys: 'raw_dir', 'lodes_dir', 'acs_dir', 'shp_dir', 'net_dir',
            'par_dir', 'lih_dir', 'rep_dir', 'nlcd_dir', 'sld_dir'

    Returns:
        Dictionary mapping directory keys to Path objects.

    Examples:
        >>> # Option 1: No directories created (recommended)
        >>> dirs = validate_data_dir('/path/to/data')
        >>> # Later, create only when needed:
        >>> lodes_dir = ensure_dir_exists(dirs['lodes_dir'])
        
        >>> # Option 2: Pre-create specific directories
        >>> dirs = validate_data_dir(
        ...     '/path/to/data',
        ...     required_dirs=['lodes_dir', 'acs_dir']
        ... )
        >>> # lodes_dir and acs_dir now exist on filesystem
    """
    dir_paths = get_data_dir_paths(data_dir)
    
    # Create only specified directories if requested
    if required_dirs:
        logger.info(f"Pre-creating directories: {required_dirs}")
        for dir_key in required_dirs:
            if dir_key in dir_paths:
                ensure_dir_exists(dir_paths[dir_key])
            else:
                logger.warning(
                    f"Unknown directory key '{dir_key}'. "
                    f"Valid keys: {list(dir_paths.keys())}"
                )
    
    return dir_paths