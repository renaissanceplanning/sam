# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 14:51:17 2022

@author: AZ7
"""

# %% Imports and globals

import pyproj
import re
import shapely.wkt
import numpy as np
import pandas as pd
import geopandas as gpd
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import Converter, localconverter
from rpy2.robjects.packages import importr

import rputils

# Import tigris, sf, and lwgeom -- these are the packages we need functions from
Rlibs = ["base","tigris","sf","lwgeom","tidycensus"]
for lib in Rlibs:
    importr(lib)
    
# Convert Nones to nulls
def _none2null(none_obj):
    return ro.r("NULL")
none_converter = Converter("None converter")
none_converter.py2rpy.register(type(None), _none2null)

# Define the global R functions
st_geometry = ro.r['st_geometry']
st_drop_geometry = ro.r['st_drop_geometry']
st_crs = ro.r['st_crs']
st_astext = ro.r['st_astext']

# %% Helpers

# dl_tiger
__TIGRIS__ = ["address_ranges","alaska_native_regional_corporations",
              "area_water","blocks","block_groups","coastline",
              "combined_statistical_areas","congressional_districts",
              "core_based_statistical_areas","counties","county_subdivisions",
              "divisions","landmarks","linear_water","metro_divisions",
              "military","nation","native_areas","new_england","places",
              "primary_roads","primary_secondary_roads","pumas","rails",
              "regions","roads","school_districts","states",
              "state_legislative_districts","tracts","tribal_block_groups",
              "tribal_census_tracts","tribal_subdivisions_national",
              "urban_areas","voting_districts","zctas"]
__TIGRIS_DEFAULT_YEAR__ = 2019

# dl_census
__TIDYCENSUS__ = ["acs","decennial","estimates","flows","pums"]
__TIDYCENSUS_DEFAULT_YEAR__ = 2019

# dl_lodes/dl_xwalk
__LODES_YEAR__ = 2019
__LODES_VERSION__ = 7
__LODES_URL__ = "https://lehd.ces.census.gov/data/lodes/LODES"

# geography equivalences between acs, tiger, and xwalk                  
__GEOGS__ = pd.DataFrame.from_dict({
    "address ranges":[np.nan,"address_ranges",np.nan,False],
    "area water":[np.nan,"area_water",np.nan,False],
    "coastline":[np.nan,"coastline",np.nan,False],
    "landmarks":[np.nan,"landmarks",np.nan,False],
    "linear water":[np.nan,"linear_water",np.nan,False],
    "metro divisions":[np.nan,"metro_divisions",np.nan,False],
    "military":[np.nan,"military","mil",False],
    "primary roads":[np.nan,"primary_roads",np.nan,False],
    "primary secondary roads":[np.nan,"primary_secondary_roads",np.nan,False],
    "rails":[np.nan,"rails",np.nan,False],
    "roads":[np.nan,"roads",np.nan,False],
    "tribal block groups":[np.nan,"tribal_block_groups",np.nan,False],
    "tribal census tracts":[np.nan,"tribal_census_tracts",np.nan,False],
    "tribal subdivisions":[np.nan,"tribal_subdivisions_national","tsub",False],
    "state":["state","states","st",True],
    "county":["county","counties","cty",True],
    "tract":["tract","tracts","trct",True],
    "block group":["block group","block_groups","bgrp",True],
    "zip code":["zcta","zctas","zcta",True],
    "block":["block","blocks","tabblk2010",True],
    "place":["place","places","stplc",True],
    "congressional district":["congressional district","congressional_districts","stcd116",True],
    "puma":["public use micodata area","pumas",np.nan,True],
    "state senate district":["state legislative district (upper chamber)","state_legislative_districts","stsldl",True], #house="upper"
    "state house district":["state legislative district (lower chamber)","state_legislative_districts","stsldu",True], #house="lower"
    "native area":["american indian area/alaska native area/hawaiian home land","native_areas","trib",True],
    "county subdivision":["county subdivision","county_subdivisions","ctycsub",True],
    "csa":["combined statistical area","combined_statistical_areas",np.nan,True],
    "ua":["urban area","urban_areas",np.nan,True],
    "elementary school district":["school district (elementary)","school_districts","stschool",True], #type="elementary"
    "secondary school district":["school district (secondary)","school_districts","stsecon",True], #type="secondary"
    "unified school district":["school district (unified)","school_districts","stschool",True], #type="unified"
    "necta":["new england city and town area","new_england","necta",True], #type="necta"
    "combined necta":["combined new england city and town area","new_england",np.nan,True], #type="combined"
    "usa":["us","nation",np.nan,True],
    "region":["region","regions",np.nan,True],
    "division":["division","divisions",np.nan,True],
    "anrc":["alaska native regional corporation","alaska_native_regional_corporations","stanrc",True],
    "voting district":["voting district","voting_districts",np.nan,True],
    "reservation":["american indian area/alaska native area (reservation or statistical entity only)","native_areas","trib",False],
    "off-reservation trust":["american indian area (off-reservation trust land only)/hawaiian home land","native_areas","trib",False],
    "cbsa":["metropolitan statistical area/micropolitan statistical_area","core_based_statistical_areas","cbsa",False],
}, orient="index", columns=["census_geog","tiger_fun","xwalk_agg","auto_census"])
__GEOGS__ = __GEOGS__.reset_index().rename(columns={"index":"level"})

# %% ACS

# class Census(rputils.WrappedDF):
#     '''
#     WrappedDF for US Census data -- stores state, year, and geographic level 
#     as metadata.
#     '''
    
#     _metadata = ["__meta__"]
    
#     def __init__(self, *args, **kwargs):
#         '''
#         Store Census data.

#         Parameters
#         ----------
#         *args, **kwargs : 
#             Used to initialize a pandas dataframe.
#         state : str, optional
#             Required metadata attribute: the state for the data. 
#         year : int, optional
#             Required metadata attribute: the year for the data.
#         level : str, optional
#             Required metadata attribute: the geographic level for the data 
#             (e.g. block group, tract).
#         geom : gpd.GeoSeries
#             Required metadata attribute: geometry associated with the table. 
#             The index of this geoseries should match the index of the table.
            
#         See also
#         --------
#         `rputils.WrappedDF`, `rputils.DFMeta`

#         Returns
#         -------
#         Census :
#             pandas dataframe of Census data, with the following metadata stored
#             as attributes in table's `__meta__` attribute:
#                 - `state`: state for the data
#                 - `year`: year for the data
#                 - `level`: geographic level for the data
#                 - `geom`: geometry associated with the data

#         '''
#         meta = rputils.DFMeta()
#         for attr_name in ["state","year","level","geom"]:
#             try:
#                 val = kwargs.pop(attr_name)
#                 setattr(meta, attr_name, val)
#             except:
#                 pass
#         kwargs["dfmeta"] = meta
#         super(Census, self).__init__(*args, **kwargs)

#     @property
#     def _constructor(self):
#         return Census
    
#     @classmethod
#     def dl_census(cls, survey, get_geom=False, **kwargs):
#         '''
#         Download Census data using the R `tidycensus` package.

#         Parameters
#         ----------
#         survey : str
#             The geography to download. Must be a survey name referenced in a 
#             `tidycensus::get_{}` function.
#         get_geom : bool, optional
#             Should a geometry be returned with this data? The default is False.
#         **kwargs
#             Passed to `tidycensus::get_{survey}`. Most commonly, these will 
#             include "geography", "table", "variables", "state", "county", and 
#             "year".

#         Returns
#         -------
#         pd.DataFrame
#             Table of survey data according to any specifications in the `kwargs`.

#         '''
#         # Check out the kwargs, and make sure they're legit
#         if survey in __TIDYCENSUS__:
#             if survey == "pums":
#                 pass
#             else:
#                 try:
#                     geog = kwargs["geography"]
#                 except:
#                     raise ValueError("need to supply geography for non-pums requests")
#                 if geog == "metropolitan statistical area" and survey == "flows":
#                     gn = "metropolitan statistical area/micropolitan statistical area"
#                     row =__GEOGS__[np.logical_and(__GEOGS__.census_geog == gn,
#                                                   ~__GEOGS__.census_geog.isna())]
#                     row.census_geog = [geog]
#                 else:
#                     row =__GEOGS__[np.logical_and(__GEOGS__.census_geog == geog,
#                                                   ~__GEOGS__.census_geog.isna())] 
#                 if len(row) == 1:
#                     kwargs["geography"] = geog
#                 else:
#                     raise ValueError(f"{geog} is not a valid tidycensus geography")
#         else:
#             raise ValueError(f"'get_{survey}' is not a valid tidycensus function")
#         # Define the tidycensus function to use
#         tidycensus_survey_fun = ro.r['_'.join(["get",survey])]
#         # Define how we get geometry
#         if get_geom == True and survey != "pums":
#             if row.auto_census.iloc[0] == True:
#                 kwargs["geometry"] = True
#                 geom_opt = "from acs"
#             else:
#                 geom_opt = "from tiger" #means it's either reservation, off-res, or cbsa
#         else:
#             geom_opt = "no geom" 
#         # Load the survey data using tidycensus. If there are any errors from the
#         # **kwargs, we'll let R handle them. 
#         if geom_opt == "no geom" or geom_opt == "from tiger":
#             # download
#             with localconverter(ro.default_converter + none_converter):
#                 df_obj = tidycensus_survey_fun(**kwargs)
#             # table
#             with localconverter(ro.default_converter + pandas2ri.converter):
#                 pd_df = ro.conversion.rpy2py(df_obj)
#             idcol = [c for c in pd_df.columns if bool(re.search("^GEOID",c))][0]
#             pd_df = pd_df.set_index(idcol)
#             # geom
#             if geom_opt == "no geom":
#                 geom_meta = gpd.GeoSeries()
#             else:
#                 geom = dl_tiger(geog=row.tiger_fun.iloc[0], year=kwargs["year"])
#                 gid = [c for c in geom.columns if bool(re.search("^GEOID",c))][0]
#                 geom = geom.set_index(gid)
#                 geom = geom[geom.index.isin(pd_df.index)]
#                 geom_meta = geom.geometry
#         else:
#             # download
#             with localconverter(ro.default_converter + none_converter):
#                 sf_obj = tidycensus_survey_fun(**kwargs)
#             # data
#             sf_df = st_drop_geometry(sf_obj)
#             with localconverter(ro.default_converter + pandas2ri.converter):
#                 pd_df = ro.conversion.rpy2py(sf_df) 
#             idcol = [c for c in pd_df.columns if bool(re.search("^GEOID",c))][0]
#             pd_df = pd_df.set_index(idcol)
#             # geom
#             sf_geometry = st_astext(st_geometry(sf_obj))
#             sf_crs = st_crs(sf_obj)
#             gpd_gs = [shapely.wkt.loads(g) for g in sf_geometry]
#             pyproj_crs = pyproj.crs.CRS(list(list(sf_crs)[1])[0])
#             geom_meta = gpd.GeoSeries(gpd_gs, crs=pyproj_crs, index=pd_df.index)          
#         # Class it
#         try:
#             state = kwargs["state"]
#         except:
#             state = "US"
#         try:
#             year = kwargs["year"]
#         except:
#             year = __TIDYCENSUS_DEFAULT_YEAR__
#         return cls(data=pd_df, state=state.upper(), year=year,
#                    level=row.level.iloc[0], geom=geom_meta)

# %% Geography crosswalk
# TODO: This works, but it leaves you hangin out to dry if you try to instantiate
# this class outside of the `dl_` function -- we can't currently validate
# without screwing up metadata inheritance
# class XWalk(rputils.WrappedDF):
#     '''
#     WrappedDF for state geography crosswalk data -- stores state as metadata.
#     '''

#     _metadata = ["__meta__"]

#     def __init__(self, *args, **kwargs):
#         '''
#         Store geography crosswalk data.

#         Parameters
#         ----------
#         *args, **kwargs : 
#             Used to initialize a pandas dataframe.
#         state : str, optional
#             Required metadata attribute: the state for the data.
        
            
#         See also
#         --------
#         `rputils.WrappedDF`, `rputils.DFMeta`

#         Returns
#         -------
#         XWalk :
#             pandas dataframe of geography crosswalk data, with the following 
#             metadata stored as attributes in table's `__meta__` attribute:
#                 - `state`: state for the data

#         '''
#         meta = rputils.DFMeta()
#         for attr_name in ["state","geom"]:
#             try:
#                 val = kwargs.pop(attr_name)
#                 setattr(meta, attr_name, val)
#             except:
#                 pass
#         kwargs["dfmeta"] = meta
#         super(XWalk, self).__init__(*args, **kwargs)

#     @property
#     def _constructor(self):
#         return XWalk        
    
#     @classmethod
#     def dl_xwalk(cls, ST):
#         '''
#         Download the geography crosswalk for a state.

#         Parameters
#         ----------
#         ST : str
#             2-letter postal code for a chosen state.

#         Returns
#         -------
#         XWalk

#         '''
#         if isinstance(ST, str):
#             ST = ST.lower()
#             if ST in ["al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id",
#                       "il","in","ia","ks","ky","la","me","md","ma","mi","mn","ms",
#                       "mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok",
#                       "or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa","wv",
#                       "wi","wy","dc"]:
#                 dl_url = f"{__LODES_URL__}{__LODES_VERSION__}/{ST}/{ST}_xwalk.csv.gz"
#                 df = pd.read_csv(dl_url, compression="gzip")
#             else:
#                 raise ValueError(f"{ST} is an invalid state")
#         else:
#             raise TypeError(f"'ST' is {type(ST)}, not str")
#         df = df.drop(columns=["blklatdd", "blklondd", "createdate"])
#         blkcol = [c for c in df.columns if bool(re.search("blk", c))][0]
#         df[blkcol] = df[blkcol].astype(str)
#         df = df.set_index(blkcol)
#         return cls(data=df, state=ST.upper())

# %% LODES

# class LODES(rputils.WrappedDF):
#     '''
#     WrappedDF for US Census LODES data.
#     '''

#     _metadata = ["__meta__"]

#     def __init__(self, *args, **kwargs):
#         '''
#         Store LODES data.

#         Parameters
#         ----------
#         *args, **kwargs : 
#             Used to initialize a pandas dataframe.
#         state : str, optional
#             Required metadata attribute: the state for the data.
#         year : int, optional
#             Required metadata attribute: the year for the data.
#         level : str, optional
#             Required metadata attribute: the geographic level for the data 
#             (e.g. block group, tract).
#         geom : gpd.GeoSeries
#             Required metadata attribute: geometry associated with the table. 
#             The index of this geoseries should match the index of the table. 
            
#         See also
#         --------
#         `rputils.WrappedDF`, `rputils.DFMeta`

#         Returns
#         -------
#         LODES :
#             pandas dataframe of LODES data, with the following metadata stored
#             as attributes in table's `__meta__` attribute:
#                 - `state`: state for the data
#                 - `year`: year for the data
#                 - `level`: geographic level for the data
#                 - `geom`: geometry associated with the data

#         '''
#         meta = rputils.DFMeta()
#         for attr_name in ["state","year","level","geom"]:
#             try:
#                 val = kwargs.pop(attr_name)
#                 setattr(meta, attr_name, val)
#             except:
#                 pass
#         kwargs["dfmeta"] = meta
#         super(LODES, self).__init__(*args, **kwargs)

#     @property
#     def _constructor(self):
#         return LODES
    
#     @classmethod
#     def dl_lodes(cls, file, ST, TYPE, YEAR, SEG=None, PART=None, 
#                  aggregate=None, get_geom=False):
#         '''
#         Download block-level employment data from LODES.

#         Parameters
#         ----------
#         file : str
#             LODES file type; see notes for options and definitions. Will be
#             converted to lower-case if not provided as such.
#         ST : str
#             2-letter postal code for a chosen state; see notes for options and
#             definitions. Will be converted to lower-case if not provided as 
#             such. Required for all files.
#         TYPE : str
#             Job type; see notes for options and definitions. Will be converted
#             to upper-case alphanumeric if not provided as such. Required for 
#             all files.
#         YEAR : int
#             4-digit year for a chosen year; see notes for options. Required for 
#             all files.
#         SEG : str, optional
#             Segment of the workforce; see notes for options and definitions. 
#             Will be converted to upper-case alphanumeric if not provided as 
#             such. Only relevant for "rac" and "wac" files, is otherwise 
#             ignored if not None.
#         PART : str
#             Part of the state file; see notes for options and definitions. Will 
#             be converted to lower-case if not provided as such. Only relevant 
#             for "od" files, is otherwise ignored if not None.
#         aggregate : str
#             Geographic level at which to report the data (e.g. block group,
#             county). Can be any geography reflected in the geography crosswalk
#             file. The default is None, which returns data at the block level.
#         get_geom : bool, optional
#             Should a geometry be returned with this data? The default is False.

#         Notes
#         -----
#         1. options for `file` are:
#             1. "od": Origin-Destination data, jobs totals are associated with 
#             both a home Census Block and a work Census Block
#             2. "rac": Residence Area Characteristic data, jobs are totaled by 
#             home Census Block
#             3: "wac": Workplace Area Characteristic data, jobs are totaled by 
#             work Census Block

#         2. options for `ST` are:
#             1. any of the 50 US states
#             2. the District of Columbia (Washington DC)
#         US territories, including Puerto Rico and the US Virgin Islands, do not
#         have employment data available through this source.

#         3. options for `SEG` are:
#             1. "S000": all workers
#             2. "SA01": workers age 29 or younger
#             3. "SA02": workers age 30 to 54
#             4. "SA03": workers age 55 or older
#             5. "SE01": workers with earnings $1250/month or less
#             6. "SE02": workers with earnings $1251/month to $3333/month
#             7. "SE03": workers with earnings greater than $3333/month
#             8. "SI01": workers in Goods-Producing industry sectors
#             9. "SI02": workers in Trade, Transportation, and Utilities industry
#             sectors
#             10. "SI03": workers in All Other Services industry sectors

#         4. options for `PART` are:
#             1. "main": includes jobs with both workplace and residence in the 
#             state
#             2. "aux": includes jobs with the workplace in the state and the
#             residence outside of the state
#         "main" and "aux" are complimentary parts of the OD file for a state.

#         5. options for `TYPE` are:
#             1. "JT00": All Jobs
#             2. "JT01": Primary Jobs
#             3. "JT02": All Private Jobs
#             4. "JT03": Private Primary Jobs
#             5. "JT04": All Federal Jobs
#             6. "JT05": Federal Primary Jobs

#         6. options for `YEAR` are generally 2002 to current year minus 3 for 
#         most files/states (LODES data is release on a 2-year lag every
#         December, so 2019 LODES will be available December 2021). Exceptions 
#         include:
#             1. Alaska has no OD or WAC data for 2017-2018
#             2. Arizona has no OD or WAC data for 2002-2003
#             3. Arkansas has no OD or WAC data for 2002
#             4. Washington DC has no OD or WAC data for 2002-2009
#             5. Massachusetts has no OD or WAC data for 2002-2010
#             6. Mississippi has no OD or WAC data for 2002-2003
#             7. New Hampshire has no OD or WAC data for 2002

#         If a specified combination of the above variables has no jobs, the file
#         will still exist, but will be empty (i.e. it will only contain the
#         header of the file, no rows of data).

#         For more information on the construction of LODES data, including
#         variable definitions for the OD, RAC, and WAC files, please see the
#         LODES technical documentation at:
#         https://lehd.ces.census.gov/data/lodes/LODES7/LODESTechDoc7.5.pdf
        
#         Returns
#         -------
#         pd.DataFrame
#             Table of block level jobs information for the input specifications.

#         '''
#         # Validate file, PART, and SEG
#         if isinstance(file, str):
#             file = file.lower()
#             if file == "od":
#                 file_message = ""
#                 SEG = None
#                 SEG_message = ""
#                 if isinstance(PART, str) or PART is None:
#                     if PART is None:
#                         PART_message = "'PART' cannot be None if 'file' is 'od'"
#                     else:
#                         PART = PART.lower()
#                         if PART in ["main", "aux"]:
#                             PART_message = ""
#                         else:
#                             PART_message = f"{PART} is an invalid 'PART' input"
#                 else:
#                     PART_message = f"'PART' is {type(PART)}, not str"
#             elif file in ["rac","wac"]:
#                 file_message = ""
#                 PART = None
#                 PART_message = ""
#                 if isinstance(SEG, str) or SEG is None:
#                     if SEG is None:
#                         SEG_message = "'SEG' cannot be None if 'file' is 'rac' or 'wac'"
#                     else:
#                         SEG = SEG.upper() 
#                         if SEG in ["S000","SA01","SA02","SA03","SE01",
#                                    "SE02","SE03","SI01","SI02","SI03"]:
#                             SEG_message = ""
#                         else:
#                             SEG_message = f"{SEG} is an invalid 'SEG' input"
#                 else:
#                     SEG_message = f"'SEG' is {type(SEG)}, not str"
#             else:
#                 file_message = f"{file} is an invalid 'file' input"
#                 PART_message = "'PART' cannot be assessed because of invalid 'file'"
#                 SEG_message = "'SEG' cannot be assessed because of invalid 'file'"
#         else:
#             file_message = f"'file' is {type(file)}, not str"
#             PART_message = "'PART' cannot be assessed because of invalid 'file'"
#             SEG_message = "'SEG' cannot be assessed because of invalid 'file'"
#         # Validate ST and YEAR
#         if isinstance(ST, str):
#             ST = ST.lower()
#             if ST in ["al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id",
#                       "il","in","ia","ks","ky","la","me","md","ma","mi","mn","ms",
#                       "mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok",
#                       "or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa","wv",
#                       "wi","wy","dc"]:
#                 ST_message = ""
#                 if isinstance(YEAR, int):
#                     if file_message == "":
#                         if file in ["od","wac"]:
#                             YEAR_bool = np.any([
#                                 np.logical_and(YEAR in np.arange(2002,2017), 
#                                                ST == "ak"),
#                                 np.logical_and(YEAR in np.arange(2004,__LODES_YEAR__+1), 
#                                                ST == "az"),
#                                 np.logical_and(YEAR in np.arange(2003,__LODES_YEAR__+1), 
#                                                ST == "ar"),
#                                 np.logical_and(YEAR in np.arange(2010,__LODES_YEAR__+1), 
#                                                ST == "dc"),
#                                 np.logical_and(YEAR in np.arange(2011,__LODES_YEAR__+1), 
#                                                ST == "ma"),
#                                 np.logical_and(YEAR in np.arange(2004,__LODES_YEAR__+1), 
#                                                ST == "ms"),
#                                 np.logical_and(YEAR in np.arange(2003,__LODES_YEAR__+1), 
#                                                ST == "nh"),
#                                 np.logical_and(YEAR in np.arange(2002,__LODES_YEAR__+1),
#                                                ST not in ["ak","az","ar","dc","ma","ms","nh"])
#                             ])
#                             if YEAR_bool == True:
#                                 YEAR_message = ""
#                             else:
#                                 YEAR_message = f"{YEAR}/{ST} is an invalid 'YEAR'/'ST' input combination"
#                         else:
#                             if YEAR in np.arange(2002,__LODES_YEAR__+1):
#                                 YEAR_message = ""
#                             else:
#                                 YEAR_message = f"{YEAR} is an invalid 'YEAR' input"    
#                     else:
#                         YEAR_message = "'YEAR' cannot be assessed because of invalid 'file'"
#                 else:
#                     YEAR_message = f"'YEAR' is {type(YEAR)}, not int"
#             else:
#                 ST_message = f"{ST} is an invalid 'ST' input"
#                 YEAR_message = "'YEAR' cannot be assessed because of invalid 'ST'"   
#         else:
#             ST_message = f"'ST' is {type(ST)}, not str"
#             YEAR_message = "'YEAR' cannot be assessed because of invalid 'ST'"
#         # Validate TYPE
#         if isinstance(TYPE, str):
#             TYPE = TYPE.upper()
#             TYPE_bool = TYPE in ["JT00","JT01","JT02","JT03","JT04","JT05"]
#             if TYPE_bool == True:
#                 TYPE_message = ""
#             else:
#                 TYPE_message = f"{TYPE} is an invalid 'TYPE' input"
#         else:
#             TYPE_message = f"'TYPE' is {type(TYPE)}, not str"
#         # Organize the error messages
#         messages = [file_message, ST_message, PART_message, 
#                     SEG_message, TYPE_message, YEAR_message]
#         errors = [" ".join(["-->", m]) for m in messages if m != ""]
#         # Raise errors, or download 
#         if len(errors) > 0:
#             msg = "\n".join(["The following errors are present in the inputs:",
#                              "\n".join(errors)])
#             raise ValueError(msg)
#         else:
#             pass
#         base_url = f"{__LODES_URL__}{__LODES_VERSION__}/{ST}/{file}"
#         if file == "od":
#             file_name = f"{ST}_{file}_{PART}_{TYPE}_{YEAR}.csv.gz"
#         else:
#             file_name = f"{ST}_{file}_{SEG}_{TYPE}_{YEAR}.csv.gz"
#         dl_url = f"{base_url}/{file_name}"
#         lodes = pd.read_csv(dl_url, compression="gzip")
#         # Aggregate if appropriate
#         lodes_ids = [c for c in lodes.columns if bool(re.search("geocode$",c))]
#         for lid in lodes_ids:
#             lodes[lid] = lodes[lid].astype(str)
#         if aggregate is None:
#             lodes = lodes.set_index(lodes_ids)
#             aggregate = "block"
#         else:
#             prefs = [c.split("geocode")[0] for c in lodes_ids]
#             try:
#                 xwc = __GEOGS__.xwalk_agg[__GEOGS__.level == aggregate].iloc[0]
#             except:
#                 raise ValueError(f"{aggregate} is an invalid aggregation level")
#             xw = XWalk.dl_xwalk(ST=ST)
#             xwid = xw.index.name
#             xw = xw.reset_index()[[xwid,xwc]].astype(str)
#             agg_ids = []
#             for lid,pref in zip(lodes_ids, prefs):
#                 nn = ''.join([pref, xwc])
#                 agg_ids.append(nn)
#                 jdf = xw.copy().rename(columns={xwid: lid, xwc: nn})
#                 lodes = lodes.astype({lid:jdf[lid].dtype})
#                 lodes = pd.merge(lodes, jdf, on=lid)
#             lodes = lodes.drop(columns=lodes_ids+["createdate"])
#             lodes = lodes.groupby(agg_ids).sum()
#         # Get geom if appropriate
#         if get_geom == True:
#             tiger_fun = __GEOGS__.tiger_fun[__GEOGS__.level == aggregate].iloc[0]
#             try:
#                 geom = dl_tiger(geog=tiger_fun, state=ST, year=YEAR)
#             except:
#                 geom = dl_tiger(geog=tiger_fun, year=YEAR)
#             gid = [c for c in geom.columns if bool(re.search("^GEOID",c))][0]
#             geom = geom.set_index(gid)
#             if file == "od":
#                 geom = geom.loc[np.logical_or(geom.index.isin(lodes.index.get_level_values(0)),
#                                               geom.index.isin(lodes.index.get_level_values(1)))]
#             else:
#                 geom = geom.loc[geom.index.isin(lodes.index)]
#             geom_meta = geom.geometry
#         else:
#             geom_meta = gpd.GeoSeries()
#         # Finalize
#         return cls(data=lodes, state=ST.upper(), year=YEAR, 
#                    level=aggregate, geom=geom_meta)
    
# %% Tiger

# Tiger isn't a class bc we don't subclass geopandas (apparently...). So
# instead it's a downloader that adds state, year, and level to the metadata.
# def dl_tiger(geog, year, **kwargs):
#     '''
#     Download Census geographies using the R `tigris` package.

#     Parameters
#     ----------
#     geom : str
#         The geography to download. Must be a name of a `tigris` function.
#     **kwargs
#         Other args passed to `tigris::{geom}`. Most commonly, these will
#         include "county" and "cb".

#     Returns
#     -------
#     gpd.GeoDataFrame
#         Shape of the `geom` according to any specifications in the `kwargs`.

#     '''
#     # Check out the kwargs, and make sure they're legit
#     if geog in __TIGRIS__:
#         pass
#     else:
#         raise ValueError(f"{geog} is not a valid tigris function")
#     # Define the tigris function to use
#     tigris_geometry_fun = ro.r[geog]
#     # Load the tiger data using tigris. If there are any errors from the
#     # **kwargs, we'll let R handle them
#     with localconverter(ro.default_converter + none_converter):
#         sf_obj = tigris_geometry_fun(**kwargs)
#     # Extract the data, the geometry, and the crs -- these will all be
#     # converted to their pythonic forms individually
#     sf_df = st_drop_geometry(sf_obj)
#     sf_geometry = st_astext(st_geometry(sf_obj))
#     sf_crs = st_crs(sf_obj)
#     # Convert the data to DataFrame, the geometry to GeoSeries, and the crs
#     # to CRS
#     with localconverter(ro.default_converter + pandas2ri.converter):
#         pd_df = ro.conversion.rpy2py(sf_df)
#     gpd_gs = [shapely.wkt.loads(g) for g in sf_geometry]
#     pyproj_crs = pyproj.crs.CRS(list(list(sf_crs)[1])[0])
#     # Form a gdf from the 3 inputs
#     gdf = gpd.GeoDataFrame(pd_df, geometry=gpd_gs, crs=pyproj_crs)
#     # Create and add the metadata
#     lev = __GEOGS__.level[__GEOGS__.tiger_fun == geog].iloc[0]
#     try:
#         state = kwargs["state"]
#     except:
#         state = "US"
#     try:
#         year = kwargs["year"]
#     except:
#         year = __TIGRIS_DEFAULT_YEAR__
#     meta = rputils.DFMeta(state=state, year=year, level=lev)
#     gdf._metadata.append("__meta__")
#     gdf.__meta__ = meta
#     # Return the gdf with metadata
#     return gdf

        
            
            
            
        
