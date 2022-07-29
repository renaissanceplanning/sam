import pandas as pd
import geopandas as gpd
from datetime import date
# from config.ref_config import par_recode
from rputils.download.fl_parcels import (fdor_gis_and_tax, 
                                         fdor_availability, 
                                         process_parcels)

# Helper Functions
# checks if a object can be a int
def is_int(element):
    try:
        int(element)
        return True
    except ValueError:
        return False

def extract_urls(county, year):    
    county_urls = fdor_availability(fdor_gis_and_tax(), 
                                    county=county, year=year)
    
    gis_url = county_urls.loc[
        (county_urls.year == year) & 
        (county_urls.file == 'GIS')][['url']].squeeze()
    nal_url = county_urls.loc[
        (county_urls.year == year) & 
        (county_urls.file == 'TaxRoll') & 
        (county_urls.url.str.contains('DBF'))][['url']].squeeze()
    
    return gis_url, nal_url
        
    
    
# Functions
# TODO ensure it can accept fips
def download_fl_parcels(county, crs, year=None, config=None):
    """Will download DOR parcels from Florida

    Args:
        county (string): County name or fips code (not working)
        crs (string): any crs representation accepted by pyproj.CRS.from_user_input
        year (int, optional): Year to pull data from. Defaults to None.
        config (dict, optional): Formates data columnes if Non returns all. 
            Defaults to None.

    Returns:
        geodataframe: cleaned parcels dataframe.
        
    Notes
    -----
    `pyproj.CRS.from_user_input` can take:
        - PROJ JSON string
        - PROJ JSON dict
        - WKT string
        - An authority string
        - An EPSG integer code
        - A tuple of (“auth_name”: “auth_code”)
        - An object with a to_json method
    Any of these would be valid inputs to the `transform_crs` parameter
    """
    if year is None:
        year = date.today().year - 1
        
    if config is None:
        config = {}
        
    # TODO convert fips to name add function
        
    gis_url, nal_url = extract_urls(county=county, year=year)
    parcels = process_parcels(gis_url=gis_url,
                              nal_url=nal_url,
                              transform_crs=crs,
                              field_specs=config)
    print(f"gis_total {parcels['gis_total']}")
    print(f"nal_total {parcels['nal_total']}")
    print(f"result_total {parcels['result_total']}")
    # add a join for recoded DOR UC
    # parcels['result'] = parcels['result'].merge(par_recode)
    
    return parcels['result']

# Test
# county='Madison'
# year=2021
# from sam.config.parcel_config import fl_par_config

# download_fl_parcels(county=county, 
#                     crs="esri:102658",
#                     year=year,
#                     config=fl_par_config
#                     )
                  