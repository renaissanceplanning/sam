import os
import geopandas as gpd
from sam.config import COUNTIES as county_shapes


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
    """Finds the county level fips and names for a give geometry

    Args:
        gdf (gpd.GeoDataFrame): A gdf containing summary area polygons

    Returns:
        tuple: A tuple containing strings for geoids and county names.
    """
    # TODO increase precision to single county
    gdf = gdf.to_crs(county_shapes.crs)
    county = county_shapes[county_shapes.intersects(gdf.dissolve().geometry[0])]
    # counties = county["COUNTYFP"].unique().tolist()
    # states = county["STATEFP"].unique().tolist()
    geoids = county["GEOID"].unique().tolist()
    county_names = county["NAME"].unique().tolist()
    # return states, counties, county_names
    return geoids, county_names


def validate_data_dir(data_dir):
    """
    Validates and creates a directory structure for storing various data sources.

    This function ensures the existence of a specific directory structure
    required to store different data sources related to various geographic data
    processing tasks. If the directories do not exist, it creates them.

    Args:
        data_dir (str): The root directory where the data structure should be created
            and validated.

    Returns:
        dict: A dictionary containing directory paths for different data sources.
            The keys in the dictionary include 'raw_dir', 'lodes_dir', 'acs_dir',
            'shp_dir', 'net_dir', 'par_dir', 'lih_dir', and 'rep_dir'.

    Example:
        >>> data_directory = '/path/to/data'
        >>> data_dirs = validate_data_dir(data_directory)
        >>> print(data_dirs)
        {'raw_dir': '/path/to/data/RAW',
         'lodes_dir': '/path/to/data/RAW/lodes',
         'acs_dir': '/path/to/data/RAW/acs',
         'shp_dir': '/path/to/data/RAW/tiger',
         'net_dir': '/path/to/data/RAW/osm',
         'par_dir': '/path/to/data/RAW/parcels',
         'lih_dir': '/path/to/data/RAW/lihtc',
         'rep_dir': '/path/to/data/RAW/replica'}

    Note:
        The function assures proper project directories are followed by creating
        directories when the appropriate directories are not created
    """
    data_dir = os.path.normpath(data_dir)
    raw_dir = os.path.join(data_dir, "RAW")
    lodes_dir = os.path.join(raw_dir, "lodes")
    acs_dir = os.path.join(raw_dir, "acs")
    shp_dir = os.path.join(raw_dir, "tiger")
    net_dir = os.path.join(raw_dir, "osm")
    par_dir = os.path.join(raw_dir, "parcels")
    lih_dir = os.path.join(raw_dir, "lihtc")
    rep_dir = os.path.join(raw_dir, "replica")
    nlcd_dir = os.path.join(raw_dir, "nlcd")
    sld_dir = os.path.join(raw_dir, "sld")

    for dire in [raw_dir, lodes_dir, acs_dir, shp_dir, net_dir, par_dir, 
                 lih_dir, rep_dir, nlcd_dir, sld_dir]:
        if os.path.exists(dire) != True:
            os.mkdir(dire)
    
    dirs = {
        'raw_dir': raw_dir,   
        'lodes_dir' :lodes_dir, 
        'acs_dir': acs_dir,    
        'shp_dir': shp_dir,    
        'net_dir': net_dir,     
        'par_dir': par_dir,    
        'lih_dir': lih_dir,
        'rep_dir': rep_dir 
    }       
            
    return dirs

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
        state: [cnt[3:] for cnt in geoids if (cnt[0:2] == state)]
        for state in states    
        }
    
    return geo_dict