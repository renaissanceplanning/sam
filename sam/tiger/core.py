# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 17:01:13 2022

@author: Aaron Weinstock
"""

import re
import geopandas as gpd

from rputils.download.census import dl_tiger

# %% Helper functions

def _tt(gdf, crs=None, trim=False, keepname=False):
    '''
    Trim, and Transform a US Census TIGER shape.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        TIGER shape.
    crs : Any, optional
        The CRS for the shape; can be anything accepted by the
        `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
        default is None, in which case the data is returned in EPSG:4269.
    trim : bool, optional
        Should only ID fields be retained? If True, GEOID will be the only
        attribute kept. The default is False.
    keepname : bool, optional
        Should "NAME" be considered an ID field? Ignored if `trim == False`.
        The default is False.

    Returns
    -------
    gpd.GeoDataFrame

    '''
    if trim == True:
        fields = [x for x in gdf.columns if bool(re.search("^GEOID",x))]
        if keepname == True:
            fields = fields+["NAME","geometry"]
        else:
            fields = fields+["geometry"]
        ttgdf = gdf[fields]
    else:
        ttgdf = gdf.copy()
    if crs is None:
        return ttgdf
    else:
        return ttgdf.to_crs(crs)

def _dtt_nation(geom, year, crs=None, trim=False, keepname=False):
    '''
    Download, Trim, and Transform a US Census TIGER shape that allows only
    nation level specifications (and up).

    Parameters
    ----------
    geom : str
        Geometry to download; passed to `dl_tiger`.
    year : int
        Year for the shape; passed to `dl_tiger`.
    crs : Any, optional
        The CRS for the shape; can be anything accepted by the
        `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
        default is None, in which case the data is returned in EPSG:4269.
    trim : bool, optional
        Should only ID fields be retained? If True, GEOID will be the only
        attribute kept. The default is False.
    keepname : bool, optional
        Should "NAME" be considered an ID field? Ignored if `trim == False`.
        The default is False.

    Returns
    -------
    gpd.GeoDataFrame

    '''
    ts = dl_tiger(geom="blocks", year=year)
    return _tt(ts, crs=crs, trim=trim, keepname=keepname)
    

def _dtt_state(geom, year, state=None, crs=None, 
               trim=False, keepname=False):
    '''
    Download, Trim, and Transform a US Census TIGER shape that allows state
    level specifications (and up).

    Parameters
    ----------
    geom : str
        Geometry to download; passed to `dl_tiger`.
    year : int
        Year for the shape; passed to `dl_tiger`.
    state : str, optional
        State for the shape; passed to `dl_tiger`. The default is None, in 
        which case the entire country's worth of data is returned.
    crs : Any, optional
        The CRS for the shape; can be anything accepted by the
        `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
        default is None, in which case the data is returned in EPSG:4269.
    trim : bool, optional
        Should only ID fields be retained? If True, GEOID will be the only
        attribute kept. The default is False.
    keepname : bool, optional
        Should "NAME" be considered an ID field? Ignored if `trim == False`.
        The default is False.

    Returns
    -------
    gpd.GeoDataFrame

    '''
    ts = dl_tiger(geom="blocks", state=state, year=year)
    return _tt(ts, crs=crs, trim=trim, keepname=keepname)

def _dtt_county(geom, year, county=None, state=None, crs=None, 
                trim=False, keepname=False):
    '''
    Download, Trim, and Transform a US Census TIGER shape that allows county
    level specifications (and up).

    Parameters
    ----------
    geom : str
        Geometry to download; passed to `dl_tiger`.
    year : int
        Year for the shape; passed to `dl_tiger`.
    county : str, or iterable of str, optional
        Counties within `state` for the shape; must be provided with a
        `state`; passed to `dl_tiger`. The default is None, in which case the 
        entire state's worth of data is returned.
    state : str, optional
        State for the shape; passed to `dl_tiger`. The default is None, in 
        which case the entire country's worth of data is returned.
    crs : Any, optional
        The CRS for the shape; can be anything accepted by the
        `GeoDataFrame.to_crs()` method, e.g. an integer EPSG code. The 
        default is None, in which case the data is returned in EPSG:4269.
    trim : bool, optional
        Should only ID fields be retained? If True, GEOID will be the only
        attribute kept. The default is False.
    keepname : bool, optional
        Should "NAME" be considered an ID field? Ignored if `trim == False`.
        The default is False.

    Returns
    -------
    gpd.GeoDataFrame

    '''
    ts = dl_tiger(geom="blocks", state=state, county=county, year=year)
    return _tt(ts, crs=crs, trim=trim, keepname=keepname)


# %% Class  

class Tiger(gpd.GeoDataFrame):
    '''
    Download TIGER shapes.
    '''
    def __init__(gdf):
        return super().__init__(gdf)
    
    @classmethod
    def blocks(cls, state, year, county=None, crs=None, trim=False):
        '''
        Download US Census blocks.

        Parameters
        ----------
        see `sam.tiger._dtt_county`

        Returns
        -------
        Tiger (subclass of gpd.GeoDataFrame)

        '''
        ts = _dtt_county(geom="blocks", state=state, county=county, year=year,
                         crs=crs, trim=trim, keepname=False)
        return cls(ts)
        
    @classmethod
    def block_groups(cls, state, county=None, year=2019, crs=None, trim=False):
        '''
        Download US Census block groups.

        Parameters
        ----------
        see `sam.tiger._dtt_county`

        Returns
        -------
        Tiger (subclass of gpd.GeoDataFrame)

        '''
        ts = _dtt_county(geom="block_groups", state=state, county=county, 
                         year=year, crs=crs, trim=trim, keepname=False)
        return cls(ts)
        
    @classmethod
    def tracts(cls, state, county=None, year=2019, crs=None, trim=False):
        '''
        Download US Census tracts.

        Parameters
        ----------
        see `sam.tiger._dtt_county`

        Returns
        -------
        Tiger (subclass of gpd.GeoDataFrame)

        '''
        ts = _dtt_county(geom="tracts", state=state, county=county, year=year,
                         crs=crs, trim=trim, keepname=False)
        return cls(ts)
        
    @classmethod
    def counties(cls, state, year=2019, crs=None, trim=False):
        '''
        Download US counties.

        Parameters
        ----------
        see `sam.tiger._dtt_state`

        Returns
        -------
        Tiger (subclass of gpd.GeoDataFrame)

        '''
        ts = _dtt_state(geom="counties", state=state, year=year,
                        crs=crs, trim=trim, keepname=True)
        return cls(ts)
    
    @classmethod
    def cbsas(cls, year=2019, crs=None, trim=False):
        '''
        Download US CBSAs.

        Parameters
        ----------
        see `sam.tiger._dtt_nation`

        '''
        ts = _dtt_county(geom="core_based_statistical_areas", year=year,
                         crs=crs, trim=trim, keepname=True)
        return cls(ts)
        
    def to_shp(self, save_path):
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
    
    
