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
    # returns clostes value 
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]


def download_nlcd(
    state, counties, year, dataset
):
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
    