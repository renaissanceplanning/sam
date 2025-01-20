import pandas as pd
import geopandas as gpd
import numpy as np
from datetime import date
from sam.config.ref_config import PAR_RECODE, FL_TO_REPLICA
from sam.config.parcel_config import (
    fl_par_config,
    fl_par_config_csv,
    fl_parcel_rename,
    fl_parcel_csv_rename,
    rep_cols,
    rep_parcel_shorten,
)
from sam.download.fl_parcels import (
    # fdor_gis_and_tax,
    # fdor_availability,
    process_parcels,
    process_parcels_csv,
    build_url
)
from sam.config import is_int


# def extract_urls(county, year):
#     urls_df = fdor_gis_and_tax()
#     county_urls = fdor_availability(df=urls_df, county=county, year=year)

#     try:
#         gis_url = county_urls.loc[
#             (county_urls.year == year)
#             & (county_urls.file == "GIS")
#             & (county_urls.url.str.contains("pin\."))
#         ][["url"]].squeeze()
#         nal_url = county_urls.loc[
#             (county_urls.year == year)
#             & (county_urls.file == "TaxRoll")
#             & (county_urls.url.str.contains("DBF"))
#             & (county_urls.url.str.contains("Final"))
#         ][["url"]].squeeze()

#         if (type(gis_url) != str) or (
#             type(gis_url) != str
#         ):  # checks to ensure that strings not sereis are returned
#             raise ValueError(
#                 f"None string url returned",
#                 f"gis type: {type(gis_url)}",
#                 f"nal type: {type(nal_url)}",
#             )

#     except:
#         gis_url = county_urls.loc[
#             (county_urls.year == year)
#             & (county_urls.file == "GIS")
#             & (county_urls.url.str.contains("pin\."))
#             & (county_urls.url.str.contains("condo") == False)
#         ][["url"]].squeeze()
#         nal_url = county_urls.loc[
#             (county_urls.year == year)
#             & (county_urls.file == "TaxRoll")
#             & (county_urls.url.str.contains(f"NAL {year}"))
#         ][["url"]].squeeze()

#         if (type(gis_url) != str) or (
#             type(gis_url) != str
#         ):  # checks to ensure that strings not sereis are returned
#             raise ValueError(
#                 f"None string url returned",
#                 f"gis type: {type(gis_url)}",
#                 f"nal type: {type(nal_url)}",
#             )

#     return gis_url, nal_url


# Functions
# TODO ensure it can accept fips
def download_fl_parcels(county, crs, year=None, config=fl_par_config, replica=True):
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

    # TODO replace when we can automate scraping the new portal.
    # gis_url, nal_url = extract_urls(county=county, year=year) 
    
    gis_url, nal_url = build_url(county=county, year=year) 
    
    parcels = process_parcels(
        gis_url=gis_url, nal_url=nal_url, transform_crs=crs, field_specs=config
    )
    print(f"gis_total {parcels['gis_total']}")
    print(f"nal_total {parcels['nal_total']}")
    print(f"result_total {parcels['result_total']}")
    # add a join for recoded DOR UC
    # parcels['result'] = parcels['result'].merge(PAR_RECODE)

    parcels["result"]["DOR_UC"] = parcels["result"]["DOR_UC"].astype(np.int64)

    if replica:
        parcels = parcels["result"].merge(FL_TO_REPLICA).copy()
        parcels = parcels.rename(columns=fl_parcel_rename)
        parcels["lat"] = parcels.centroid.y
        parcels["lng"] = parcels.centroid.x
        parcels["BLOCKGROUP"] = parcels["BLOCKGROUP"].str.zfill(12)
        parcels["TRACT"] = parcels["BLOCKGROUP"].str.slice(0, 10)
        parcels = parcels[rep_cols]
        parcels = parcels.rename(columns=rep_parcel_shorten)

    else:
        parcels = parcels["result"].merge(PAR_RECODE).copy()

    return parcels


def download_old_fl_parcels(
    gis_url, nal_url, crs, config=fl_par_config_csv, replica=True
):
    parcels = process_parcels_csv(
        gis_url=gis_url, nal_url=nal_url, transform_crs=crs, field_specs=config
    )
    print(f"gis_total {parcels['gis_total']}")
    print(f"nal_total {parcels['nal_total']}")
    print(f"result_total {parcels['result_total']}")
    # add a join for recoded DOR UC
    # parcels['result'] = parcels['result'].merge(PAR_RECODE)

    parcels["result"]["DOR_UC"] = parcels["result"]["DOR_UC"].astype(np.int64)

    if replica:
        parcels = parcels["result"].merge(FL_TO_REPLICA).copy()
        parcels = parcels.rename(columns=fl_parcel_csv_rename)
        parcels["lat"] = parcels.centroid.y
        parcels["lng"] = parcels.centroid.x
        parcels["BLOCKGROUP"] = parcels["BLOCKGROUP"].str.zfill(12)
        parcels["TRACT"] = parcels["BLOCKGROUP"].str.slice(0, 10)
        parcels = parcels[rep_cols]
        parcels = parcels.rename(columns=rep_parcel_shorten)

    else:
        parcels = parcels["result"].merge(PAR_RECODE).copy()

    return parcels

# def process_permits(path, 
#                     address_fields = ['Address'],
#                     sqft_fields = ['HSF', 'UHSF'],
#                     unit_fields = ['Unit'],
#                     land_use_fields = [],
#                     land_use_dict = {
#                         'res_uses' = [],
#                         'non_resuses' = []
#                     },
#                     ):
#     pass

# [{'tigerLine': {'side': 'L', 'tigerLineId': '178479986'}, 
#   'coordinates': {'x': -80.2490817848835, 'y': 33.0127196588559}, 
#   'addressComponents': {'zip': '29483', 'streetName': 'CHAUSSEE', 'preType': '', 'city': 'KNIGHTSVILLE', 'preDirection': '', 'suffixDirection': '', 'fromAddress': '201', 'state': 'SC', 'suffixType': 'BLVD', 'toAddress': '299', 'suffixQualifier': '', 'preQualifier': ''}, 
#   'matchedAddress': '207 CHAUSSEE BLVD, KNIGHTSVILLE, SC, 29483'},
  
#  {'tigerLine': {'side': 'L', 'tigerLineId': '178479986'}, 
#   'coordinates': {'x': -80.2490817848835, 'y': 33.0127196588559}, 
#   'addressComponents': {'zip': '29483', 'streetName': 'CHAUSSEE', 'preType': '', 'city': 'SUMMERVILLE', 'preDirection': '', 'suffixDirection': '', 'fromAddress': '201', 'state': 'SC', 'suffixType': 'BLVD', 'toAddress': '299', 'suffixQualifier': '', 'preQualifier': ''}, 
#   'matchedAddress': '207 CHAUSSEE BLVD, SUMMERVILLE, SC, 29483'}]

# '1503 Spicata St, Mount Pleasant'