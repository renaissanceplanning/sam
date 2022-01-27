# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 17:01:13 2022

@author: AZ7
"""

import os
import re
import geopandas as gpd
from pyproj import CRS
from warnings import warn

from rputils.download.census import dl_tiger

# %% Globals

mapper = {"block_groups":"block_groups",
          "blocks":"blocks",
          "tracts":"tracts",
          "counties":"counties",
          "cbsas":"core_based_statistical_areas"}

# %% Function    

class tiger(gpd.GeoDataFrame):
    '''
    Download a standardized version of various TIGER shapes.
    '''
    def __init__(geography, year, state=None, county=None, crs=None):
        '''
        Download a standardized TIGER shape.

        Parameters
        ----------
        geography : str
            Geography for the shape; currently supported are "blocks",
            "block_groups", "tracts", "counties", and "cbsas".
        year : int
            Year for the shape.
        state : str, optional
            State for the shape; ignored if `geography=="cbsas"`. The default
            is None, in which case the entire country's worth of data is 
            returned.
        county : str, or iterable of str, optional
            Counties within `state` for the shape; must be provided with a
            `state`, and ignored if `geography=="cbsas"`. The default is None,
            in which case the entire state's worth of data is returned.
        crs : Any, optional
            The CRS for the shape; can be anything accepted by
            `pyproj.CRS.from_user_input`, e.g. an integer EPSG code. The 
            default is None, in which case the data is returned in EPSG:4269.

        Returns
        -------
        gpd.GeoDataFrame
            A geodataframe of the shape, with a GEOID file and -- if
            `geography in ["counties","cbsas"]`, a "NAME" field.

        '''
        # Load tiger 
        gl = geography.lower.replace(" ","_")
        try:
            fun = mapper[gl]
        except:
            raise ValueError(f"{geography} is an invalid geography, must be "\
                             f"one of {', '.join(mapper.keys())}")
        if state is None and county is not None:
            warn("Counties provided without state; they will be ignored")
            county = None
        else:
            pass
        if geography == "cbsas":
            ts = dl_tiger(geom=fun, year=year)
        else:
            ts = dl_tiger(geom=fun, state=state, year=year, county=county)
        # Subset fields 
        # TODO: separate method for this?
        fields = [x for x in ts.columns if bool(re.search("^GEOID",x))]
        if geography in ["cbsas","county"]:
            fields = fields+["NAME"]
        else:
            pass
        ts = ts[fields+["geometry"]]
        # Transform
        if crs is None:
            pass
        else:
            try:
                crs = CRS.from_user_input()
            except:
                raise ValueError(f"CRS cannot be made from {crs}")
        # Return
        ts = ts.to_crs(crs)
        return ts
    
    def to_shapefile(self, save_path):
        '''
        Write the standardized TIGER shape to shapefile.

        Parameters
        ----------
        save_path : path
            File path at which to save the shape.

        Returns
        -------
        None.

        '''
        self.to_file(save_path)
        return None
