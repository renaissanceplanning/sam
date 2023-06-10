import os

import geopandas as gpd

from sam.config import COUNTIES as county_shapes


def is_int(element):
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
        tuple: A tuple containing strings for state and county fips, and county
            names.
    """
    # TODO increase precision to single county
    gdf = gdf.to_crs(county_shapes.crs)
    county = county_shapes[county_shapes.intersects(gdf.dissolve().geometry[0])]
    counties = county["COUNTYFP"].unique().tolist()
    states = county["STATEFP"].unique().tolist()
    county_names = county["NAME"].unique().tolist()
    return states, counties, county_names


def validate_data_dir(data_dir):
    data_dir = os.path.normpath(data_dir)
    raw_dir = os.path.join(data_dir, "RAW")
    lodes_dir = os.path.join(raw_dir, "lodes")
    acs_dir = os.path.join(raw_dir, "acs")
    shp_dir = os.path.join(raw_dir, "tiger")
    net_dir = os.path.join(raw_dir, "osm")
    par_dir = os.path.join(raw_dir, "parcels")
    lih_dir = os.path.join(raw_dir, "lihtc")

    for dire in [raw_dir, lodes_dir, acs_dir, shp_dir, net_dir, par_dir, lih_dir]:
        if os.path.exists(dire) != True:
            os.mkdir(dire)
