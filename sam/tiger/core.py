# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 17:01:13 2022

@author: Aaron Weinstock
"""

import re
import geopandas as gpd

from rputils.download.census import dl_tiger

# %% Function    

class Tiger(gpd.GeoDataFrame):
    '''
    Download TIGER shapes.
    '''
    def __init__(gdf):
        return super().__init__(gdf)
    
    @classmethod
    def blocks(cls, state, county=None, year=2019, crs=None, trim=False):
        '''
        Download US Census blocks.

        Parameters
        ----------
        state : str, optional
            State for the shape. The default is None, in which case the entire 
            country's worth of data is returned.
        county : str, or iterable of str, optional
            Counties within `state` for the shape; must be provided with a
            `state`. The default is None, in which case the entire state's 
            worth of data is returned.
        year : int
            Year for the shape. The default is 2019.
        crs : Any, optional
            The CRS for the shape; can be anything accepted by the
            `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
            default is None, in which case the data is returned in EPSG:4269.
        trim : bool
            Should only ID fields be retained? If True, GEOID will be the only
            attribute kept. The default is False.

        Returns
        -------
        gpd.GeoDataFrame

        '''
        ts = dl_tiger(geom="blocks", state=state, county=county, year=year)
        if trim == True:
            fields = [x for x in ts.columns if bool(re.search("^GEOID",x))]
            fields = fields+["geometry"]
            ts = ts[fields]
        else:
            pass
        if crs is None:
            return cls(ts)
        else:
            return cls(ts.to_crs(crs))
        
    @classmethod
    def block_groups(cls, state, county=None, year=2019, crs=None, trim=False):
        '''
        Download US Census block groups.

        Parameters
        ----------
        state : str, optional
            State for the shape. The default is None, in which case the entire 
            country's worth of data is returned.
        county : str, or iterable of str, optional
            Counties within `state` for the shape; must be provided with a
            `state`. The default is None, in which case the entire state's 
            worth of data is returned.
        year : int
            Year for the shape. The default is 2019.
        crs : Any, optional
            The CRS for the shape; can be anything accepted by the
            `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
            default is None, in which case the data is returned in EPSG:4269.
        trim : bool
            Should only ID fields be retained? If True, GEOID will be the only
            attribute kept. The default is False.

        Returns
        -------
        gpd.GeoDataFrame

        '''
        ts = dl_tiger(geom="block_groups", state=state, county=county, year=year)
        if trim == True:
            fields = [x for x in ts.columns if bool(re.search("^GEOID",x))]
            fields = fields+["geometry"]
            ts = ts[fields]
        else:
            pass
        if crs is None:
            return cls(ts)
        else:
            return cls(ts.to_crs(crs))
        
    @classmethod
    def tracts(cls, state, county=None, year=2019, crs=None, trim=False):
        '''
        Download US Census tracts.

        Parameters
        ----------
        state : str, optional
            State for the shape. The default is None, in which case the entire 
            country's worth of data is returned.
        county : str, or iterable of str, optional
            Counties within `state` for the shape; must be provided with a
            `state`. The default is None, in which case the entire state's 
            worth of data is returned.
        year : int
            Year for the shape. The default is 2019.
        crs : Any, optional
            The CRS for the shape; can be anything accepted by the
            `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
            default is None, in which case the data is returned in EPSG:4269
        trim : bool
            Should only ID fields be retained? If True, GEOID will be the only
            attribute kept. The default is False.

        Returns
        -------
        gpd.GeoDataFrame

        '''
        ts = dl_tiger(geom="tracts", state=state, county=county, year=year)
        if trim == True:
            fields = [x for x in ts.columns if bool(re.search("^GEOID",x))]
            fields = fields+["geometry"]
            ts = ts[fields]
        else:
            pass
        if crs is None:
            return cls(ts)
        else:
            return cls(ts.to_crs(crs))
        
    @classmethod
    def counties(cls, state, year=2019, crs=None, trim=False):
        '''
        Download US counties.

        Parameters
        ----------
        state : str, optional
            State for the shape. The default is None, in which case the entire 
            country's worth of data is returned.
        year : int
            Year for the shape. The default is 2019.
        crs : Any, optional
            The CRS for the shape; can be anything accepted by the
            `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
            default is None, in which case the data is returned in EPSG:4269.
        trim : bool
            Should only ID fields be retained? If True, GEOID and NAME will be 
            the only attributes kept. The default is False.

        Returns
        -------
        gpd.GeoDataFrame

        '''
        ts = dl_tiger(geom="counties", state=state, year=year)
        if trim == True:
            fields = [x for x in ts.columns if bool(re.search("^GEOID",x))]
            fields = fields+["NAME","geometry"]
            ts = ts[fields]
        else:
            pass
        if crs is None:
            return cls(ts)
        else:
            return cls(ts.to_crs(crs))
    
    @classmethod
    def cbsas(cls, year=2019, crs=None, trim=False):
        '''
        Download US CBSAs.

        Parameters
        ----------
        year : int
            Year for the shape. The default is 2019.
        crs : Any, optional
            The CRS for the shape; can be anything accepted by the
            `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
            default is None, in which case the data is returned in EPSG:4269.
        trim : bool
            Should only ID fields be retained? If True, GEOID and NAME will be 
            the only attributes kept. The default is False.

        Returns
        -------
        gpd.GeoDataFrame

        '''
        ts = dl_tiger(geom="core_based_statistical_areas", year=year)
        if trim == True:
            fields = [x for x in ts.columns if bool(re.search("^GEOID",x))]
            fields = fields+["NAME","geometry"]
            ts = ts[fields]
        else:
            pass
        if crs is None:
            return cls(ts)
        else:
            return cls(ts.to_crs(crs))
        
    def to_shapefile(self, save_path):
        '''
        Write a TIGER shape to shapefile.

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
    
    
