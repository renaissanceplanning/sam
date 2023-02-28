"""
Created on Thu Jan 27 15:44:09 2022

@author: Aaron Weinstock
"""

"""
'land cover change index', 'land cover all years', 'land cover',
       'land cover change', 'land cover change pixels',
       'developed imperviousness all years', 'developed imperviousness',
       'developed imperviousness descriptor',
       'developed urban descriptor', 'developed imperviousness change',
       'tree canopy cover', 'tree canopy change'
"""

import os
import pandas as pd
import geopandas as gpd
import numpy as np

from sam.download.nlcd import dl_nlcd
from sam.config import COUNTIES as county_shapes
from shapely import geometry

def closest(lst, K):
    """
    Find the value in the list `lst` that is closest to the given value `K`.
    
    Args:
    lst (list): A list of numeric values.
    K (numeric): A numeric value to find the closest value to.
    
    Returns:
    The value in `lst` that is closest to `K`.
    """
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]


def download_nlcd(
    state, counties, year, dataset
):
    """
    Download National Land Cover Database (NLCD) data for a given state, list of counties, year, and dataset.

    Parameters:
    state (str): Two-letter state abbreviation.
    counties (list): List of three-digit FIPS county codes for the desired counties.
    year (int): Year of NLCD data desired. Will automatically choose the closest year available.
    dataset (str): Type of NLCD data desired (e.g. "landcover", "impervious"), full list
        of avaliable NLCD data is below.
        
    NLCD Data Sets:
    - 'land cover change index' 
    - 'land cover all years' 
    - 'land cover'
    - 'land cover change' 
    - 'land cover change pixels'
    - 'developed imperviousness all years'
    - 'developed imperviousness'
    - 'developed imperviousness descriptor'
    - 'developed urban descriptor'
    - 'developed imperviousness change'
    - 'tree canopy cover'
    - 'tree canopy change'

    Returns:
    raster (algi.raster): NLCD data for the specified state and counties. 

    """
    if state == '72':
        geog = "puerto rico"
    if state == "02":
        geog = "alaska"
    else:
        geog = "conus"
    
    year = closest(lst=[2019,2016,2013,2011,2008,2006,2004,2001],
                   K=year)
    
    cnties = county_shapes.loc[(county_shapes.STATEFP.isin(state)) & 
                               (county_shapes.COUNTYFP.isin(counties))]
    
    bounds = cnties.total_bounds
    
    dict = {'id': ['clt'],
        'geometry': [geometry.box(
    bounds[0],
    bounds[1], 
    bounds[2], 
    bounds[3]
    )]}
    
    bbox = gpd.GeoDataFrame(
        dict,
        crs = cnties.crs
    ).to_crs("EPSG:4326")
    
    raster = dl_nlcd(dataset=dataset, 
                     geog=geog, 
                     year=year, 
                     window=bbox, 
                     mask=False)
    
    return raster

if __name__ == "__main__":
    state = ['37']
    counties = ['069', '183', '063', '101']
    county_names = ['Franklin', 'Wake', 'Durham', 'Johnston']
    
    nlcd = download_nlcd(state = state, 
                         counties=counties, 
                         year=2020, 
                         dataset='developed imperviousness')
    