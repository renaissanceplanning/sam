# -*- coding: utf-8 -*-
"""
Created on Wed Jul 12 12:20:53 2023

@author: w_rpg
"""

# %% Imports

from bs4 import BeautifulSoup
import geopandas as gpd
from io import BytesIO
import numpy as np
import pandas as pd
from pyproj import CRS
import re
import requests
from shapely.geometry import Point
from urllib.request import Request, urljoin, urlopen
from zipfile import ZipFile

# %% Globals

# These are the main URLs for the two SNAP functions; set as globals in case
# the path ever changes
SNAP_RETAILERS_MAIN_PAGE = "https://www.fns.usda.gov/snap/retailer/historicaldata"
SNAP_STORE_TYPES_MAIN_PAGE = "https://www.fns.usda.gov/snap/store-definitions"

# %% Functions

def download_snap_retailers(current=True, mask=None, return_as_shape=False):
    '''
    Download "historical data on authorized SNAP retailers" from the U.S.
    Department of Agriculture Food and Nutrition Service.

    Parameters
    ----------
    current : bool, optional
        Should only currently authorized SNAP retailers be returned? The 
        default is True.
    mask : gpd.GeoDataFrame or gpd.GeoSeries, optional
        A mask for the SNAP retailers; if provided, only SNAP retailers that
        lie within the mask will be returned. The default is None.
    return_as_shape : bool, optional
        Should the data be returned as a shape (gpd.GeoDataFrame)? The default 
        is False (returned as pd.DataFrame).
    
    Details
    -------
    The Supplemental Nutrition Assistance Program, or SNAP, "provides food 
    benefits to low-income families to supplement their grocery budget so 
    they can afford the nutritious food essential to health and well-being".
    It is managed by the U.S. Department of Agriculture 
    Food and Nutrition Service (FNS). For more information on SNAP, check out
    https://www.fns.usda.gov/snap/supplemental-nutrition-assistance-program.
    
    FNS keeps an archive of "retailer name, type, address, location and 
    authorization dates for retailers that were authorized to accept SNAP 
    benefits at any point since 1990". This function will download that
    archive, filtering and masking as indicated by the parameters. See
    https://www.fns.usda.gov/snap/retailer/historicaldata for more information.
    
    The dataset contains the following attributes:
        - Record ID: unique ID for the retailer
        - Store Name: retailer name
        - Store Type: SNAP store type of the retailer
        - Street Number/Street Name/Additional Address/City/State/Zip Code/Zip4: 
          retailer address
        - County: county in which the retailer is located
        - Latitude/Longitude: point coordinates for the retailer
        - Authorization Date: day on which retailer entered SNAP
        - End Date: day on which retailer left SNAP; " " indicates that the
          retailer is still SNAP authorized
    
    All attributes will be retained in the result, regardless of parameters 
    provided. Changes in the parameters will only change the number of records 
    and data type returned.
    
    For descriptions of the SNAP store type designations, refer to the function
    `snap_store_types`.    
    
    Returns
    -------
    [g]pd.[Geo]DataFrame, depending on the `return_as_shape` parameter.

    '''
    # Scan the "SNAP historical data" page for a zip file -- the data we 
    # want is the only zip on the page, so we can just search until we find it
    req = Request(SNAP_RETAILERS_MAIN_PAGE)
    html_page = urlopen(req)
    soup = BeautifulSoup(html_page, "lxml")
    for link in soup.find_all("a", href=True):
        if link.has_attr("href"):
            file = link["href"]
            if bool(re.search(".zip$", file)) == True:
                zip_link = urljoin(SNAP_RETAILERS_MAIN_PAGE, file)
                break
    # Identify the .csv in the zip folder
    req_zip_link = requests.get(zip_link, stream=True)
    zip_open = ZipFile(BytesIO(req_zip_link.content))
    zip_files = zip_open.namelist()
    w_csv = np.where([bool(re.search(".csv$", f)) for f in zip_files])[0][0]
    csv = zip_files[w_csv]
    # Download the csv from the zipfile
    snap = pd.read_csv(zip_open.open(csv))
    # Filter to only currently authorized retailers, if applicable 
    if current == True:
        snap = snap.loc[snap["End Date"] == " "]
    # Convert to shape, UNLESS there's no mask AND return as shape is False.
    # After converting to shape, mask if requested and return appropriately
    if mask is None and return_as_shape == False:
        return snap
    else:
        # Geometrize
        snap_geom = gpd.GeoSeries(
            [Point(lat,lon) for lat,lon in zip(snap.Latitude,snap.Longitude)],
            crs=4326,
            index=snap.index
        )
        snap_gpd = gpd.GeoDataFrame(snap, geometry=snap_geom)
        if mask is None:
            return snap_gpd
        else:
            # Mask and return
            latlon = CRS.from_epsg(4326)
            if mask.crs.equals(latlon):
                mask_4326 = mask.copy()
                back_convert = False
            else:
                mask_4326 = mask.to_crs(4326)
                back_convert = True
            if isinstance(mask_4326, gpd.GeoSeries):
                mask_4326 = gpd.GeoDataFrame({"geometry":mask_4326})
            else:
                mask_4326 = mask_4326.loc[:, ["geometry"]]
            snap_masked = gpd.overlay(snap_gpd, mask_4326, how="intersection")
            if back_convert == True:
                snap_masked = snap_masked.to_crs(mask.crs)
            if return_as_shape == True:
                return snap_masked
            else:
                return snap_masked.drop(columns="geometry")
            
def snap_store_types():
    '''
    Return descriptions of SNAP store types, and 2-letter codes associated 
    with each.

    Details
    -------
    SNAP retailers are classified into store types based on "how the store 
    operates its business". 
    
    The dataset contains the following attributes:
        - Store Type: SNAP store type
        - Store Code: 2-letter code associated with the Store Type
        - Definition: description of the business of the Store Type

    Returns
    -------
    pd.DataFrame

    '''
    df = pd.read_html(SNAP_STORE_TYPES_MAIN_PAGE, header=0)[0]
    df = df.loc[:, ["Store Type","Store Code","Definition"]]
    return df
    
    
        
        
        
        
