# -*- coding: utf-8 -*-
"""
Created on Mon Jan 24 13:59:55 2022

@author: Aaron Weinstock
"""

# TODO: this deprecates census.geom and census.geometries
# TODO: this deprecates download.lodes and download.lodes_class
# TODO: get R libs in the environment.yml, then just load these

# %% Imports
import os
import pyproj
import shapely.wkt
import numpy as np
import pandas as pd
import geopandas as gpd
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import Converter, localconverter
from rpy2.robjects.packages import importr
from sam.config import is_int
from sam.config import CENSUS_API_KEY

# Import tigris, sf, and lwgeom -- these are the packages we need functions from
Rlibs = ["base", "tigris", "sf", "lwgeom", "tidycensus"]
for lib in Rlibs:
    importr(lib)
    if lib == "tidycensus":
        tidy = importr(lib)
        tidy.census_api_key(CENSUS_API_KEY, install=True, overwrite=True)
        print(f"API key set: {CENSUS_API_KEY}")
    

# Convert Nones to nulls
def _none2null(none_obj):
    return ro.r("NULL")


none_converter = Converter("None converter")
none_converter.py2rpy.register(type(None), _none2null)

# Define the global R functions
st_geometry = ro.r["st_geometry"]
st_drop_geometry = ro.r["st_drop_geometry"]
st_crs = ro.r["st_crs"]
st_astext = ro.r["st_as_text"]

# %% Global configurations

# dl_tiger
__TIGRIS__ = [
    "address_ranges",
    "alaska_native_regional_corporations",
    "area_water",
    "blocks",
    "block_groups",
    "coastline",
    "combined_statistical_areas",
    "congressional_districts",
    "core_based_statistical_areas",
    "counties",
    "county_subdivisions",
    "divisions",
    "landmarks",
    "linear_water",
    "metro_divisions",
    "military",
    "nation",
    "native_areas",
    "new_england",
    "places",
    "primary_roads",
    "primary_secondary_roads",
    "pumas",
    "rails",
    "regions",
    "roads",
    "school_districts",
    "states",
    "state_legislative_districts",
    "tracts",
    "tribal_block_groups",
    "tribal_census_tracts",
    "tribal_subdivisions_national",
    "urban_areas",
    "voting_districts",
    "zctas",
]

# dl_census
__TIDYCENSUS__ = ["acs", "decennial", "estimates", "flows", "pums"]

# dl_lodes/dl_xwalk
__LODES_YEAR__ = 2022
__LODES_VERSION__ = 8
__LODES_URL__ = "https://lehd.ces.census.gov/data/lodes/LODES"


# %% Functions


def dl_tiger(geom, **kwargs):
    """
    Download Census geographies using the R `tigris` package.

    Parameters
    ----------
    geom : str
        The geography to download. Must be a name of a `tigris` function.
    **kwargs
        Passed to `tigris::{geom}`. Most commonly, these will include
        "state", "county", "year", and "cb".

    Returns
    -------
    gpd.GeoDataFrame
        Shape of the `geom` according to any specifications in the `kwargs`.

    """
    # convert 5 digit county codes into 3 digit for tigris
    # TODO extract to function
    if "county" in kwargs:
        if isinstance(kwargs["county"], list):
            kwargs["county"] = [
                county[-3:] if is_int(county) & (len(county) > 3) else county
                for county in kwargs["county"]
            ]
        else:
            if is_int(kwargs["county"]) & (len(kwargs["county"]) > 3):
                kwargs["county"] = kwargs["county"][-3:]

    # Check out the kwargs, and make sure they're legit
    if geom in __TIGRIS__:
        pass
    else:
        raise ValueError(f"'{geom}' is not a valid tigris function")
    # Define the tigris function to use
    tigris_geometry_fun = ro.r[geom]
    # Load the tiger data using tigris. If there are any errors from the
    # **kwargs, we'll let R handle them
    with localconverter(ro.default_converter + none_converter):
        sf_obj = tigris_geometry_fun(**kwargs)
    # Extract the data, the geometry, and the crs -- these will all be
    # converted to their pythonic forms individually
    sf_df = st_drop_geometry(sf_obj)
    sf_geometry = st_astext(st_geometry(sf_obj))
    sf_crs = st_crs(sf_obj)
    # Convert the data to DataFrame, the geometry to GeoSeries, and the crs
    # to CRS
    with localconverter(ro.default_converter + pandas2ri.converter):
        pd_df = ro.conversion.rpy2py(sf_df)
    gpd_gs = [shapely.wkt.loads(g) for g in sf_geometry]
    pyproj_crs = pyproj.crs.CRS(list(list(sf_crs)[1])[0])
    # Form a gdf from the 3 inputs
    gdf = gpd.GeoDataFrame(pd_df, geometry=gpd_gs, crs=pyproj_crs)
    return gdf


def dl_census(survey, **kwargs):
    """
    Download Census data using the R `tidycensus` package.

    Parameters
    ----------
    survey : str
        The geography to download. Must be a survey name referenced in a
        `tidycensus::get_{}` function.
    **kwargs
        Passed to `tidycensus::get_{survey}`. Most commonly, these will
        include "geography", "table", "variables", "state", "county", and
        "year".

    Returns
    -------
    pd.DataFrame
        Table of survey data according to any specifications in the `kwargs`.

    """
    if ("county" in kwargs) & (kwargs["county"] is not None):
        if isinstance(kwargs["county"], list):
            kwargs["county"] = [
                county[-3:] if is_int(county) & (len(county) > 3) else county
                for county in kwargs["county"]
            ]
        else:
            if is_int(kwargs["county"]) & (len(kwargs["county"]) > 3):
                kwargs["county"] = kwargs["county"][-3:]

    # if 'county' in kwargs:
    #     kwargs['county'] = ro.vectors.StrVector(kwargs['county'])
    # Check out the kwargs, and make sure they're legit
    if survey in __TIDYCENSUS__:
        pass
    else:
        raise ValueError(f"'get_{survey}' is not a valid tidycensus function")
    # Define the tidycensus function to use
    tidycensus_survey_fun = ro.r["_".join(["get", survey])]
    # Load the survey data using tidycensus. If there are any errors from the
    # **kwargs, we'll let R handle them
    with localconverter(ro.default_converter + none_converter):
        df_obj = tidycensus_survey_fun(**kwargs)
    # Convert the data to DataFrame
    with localconverter(ro.default_converter + pandas2ri.converter):
        pd_df = ro.conversion.rpy2py(df_obj)
    return pd_df


def dl_lodes(file, ST, TYPE, YEAR, SEG=None, PART=None):
    """
    Download block-level employment data from LODES.

    Parameters
    ----------
    file : str
        LODES file type; see notes for options and definitions. Will be
        converted to lower-case if not provided as such.
    ST : str
        2-letter postal code for a chosen state; see notes for options and
        definitions. Will be converted to lower-case if not provided as
        such. Required for all files.
    TYPE : str
        Job type; see notes for options and definitions. Will be converted
        to upper-case alphanumeric if not provided as such. Required for
        all files.
    YEAR : int
        4-digit year for a chosen year; see notes for options. Required for
        all files.
    SEG : str, optional
        Segment of the workforce; see notes for options and definitions.
        Will be converted to upper-case alphanumeric if not provided as
        such. Only relevant for "rac" and "wac" files, is otherwise
        ignored if not None.
    PART : str
        Part of the state file; see notes for options and definitions. Will
        be converted to lower-case if not provided as such. Only relevant
        for "od" files, is otherwise ignored if not None.

    Notes
    -----
    1. options for `file` are:
        1. "od": Origin-Destination data, jobs totals are associated with
        both a home Census Block and a work Census Block
        2. "rac": Residence Area Characteristic data, jobs are totaled by
        home Census Block
        3: "wac": Workplace Area Characteristic data, jobs are totaled by
        work Census Block

    2. options for `ST` are:
        1. any of the 50 US states
        2. the District of Columbia (Washington DC)
    US territories, including Puerto Rico and the US Virgin Islands, do not
    have employment data available through this source.

    3. options for `SEG` are:
        1. "S000": all workers
        2. "SA01": workers age 29 or younger
        3. "SA02": workers age 30 to 54
        4. "SA03": workers age 55 or older
        5. "SE01": workers with earnings $1250/month or less
        6. "SE02": workers with earnings $1251/month to $3333/month
        7. "SE03": workers with earnings greater than $3333/month
        8. "SI01": workers in Goods-Producing industry sectors
        9. "SI02": workers in Trade, Transportation, and Utilities industry
        sectors
        10. "SI03": workers in All Other Services industry sectors

    4. options for `PART` are:
        1. "main": includes jobs with both workplace and residence in the
        state
        2. "aux": includes jobs with the workplace in the state and the
        residence outside of the state
    "main" and "aux" are complimentary parts of the OD file for a state.

    5. options for `TYPE` are:
        1. "JT00": All Jobs
        2. "JT01": Primary Jobs
        3. "JT02": All Private Jobs
        4. "JT03": Private Primary Jobs
        5. "JT04": All Federal Jobs
        6. "JT05": Federal Primary Jobs

    6. options for `YEAR` are generally 2002 to current year minus 3 for
    most files/states (LODES data is release on a 2-year lag every
    December, so 2019 LODES will be available December 2021). Exceptions
    include:
        1. Alaska has no OD or WAC data for 2017-2018
        2. Arizona has no OD or WAC data for 2002-2003
        3. Arkansas has no OD or WAC data for 2002
        4. Washington DC has no OD or WAC data for 2002-2009
        5. Massachusetts has no OD or WAC data for 2002-2010
        6. Mississippi has no OD or WAC data for 2002-2003
        7. New Hampshire has no OD or WAC data for 2002

    If a specified combination of the above variables has no jobs, the file
    will still exist, but will be empty (i.e. it will only contain the
    header of the file, no rows of data).

    For more information on the construction of LODES data, including
    variable definitions for the OD, RAC, and WAC files, please see the
    LODES technical documentation at:
    https://lehd.ces.census.gov/data/lodes/LODES7/LODESTechDoc7.5.pdf

    Returns
    -------
    pd.DataFrame
        Table of block level jobs information for the input specifications.

    """
    # Validate file, PART, and SEG
    if isinstance(file, str):
        file = file.lower()
        if file == "od":
            file_message = ""
            SEG = None
            SEG_message = ""
            if isinstance(PART, str) or PART is None:
                if PART is None:
                    PART_message = "'PART' cannot be None if 'file' is 'od'"
                else:
                    PART = PART.lower()
                    if PART in ["main", "aux"]:
                        PART_message = ""
                    else:
                        PART_message = f"{PART} is an invalid 'PART' input"
            else:
                PART_message = f"'PART' is {type(PART)}, not str"
        elif file in ["rac", "wac"]:
            file_message = ""
            PART = None
            PART_message = ""
            if isinstance(SEG, str) or SEG is None:
                if SEG is None:
                    SEG_message = "'SEG' cannot be None if 'file' is 'rac' or 'wac'"
                else:
                    SEG = SEG.upper()
                    if SEG in [
                        "S000",
                        "SA01",
                        "SA02",
                        "SA03",
                        "SE01",
                        "SE02",
                        "SE03",
                        "SI01",
                        "SI02",
                        "SI03",
                    ]:
                        SEG_message = ""
                    else:
                        SEG_message = f"{SEG} is an invalid 'SEG' input"
            else:
                SEG_message = f"'SEG' is {type(SEG)}, not str"
        else:
            file_message = f"{file} is an invalid 'file' input"
            PART_message = "'PART' cannot be assessed because of invalid 'file'"
            SEG_message = "'SEG' cannot be assessed because of invalid 'file'"
    else:
        file_message = f"'file' is {type(file)}, not str"
        PART_message = "'PART' cannot be assessed because of invalid 'file'"
        SEG_message = "'SEG' cannot be assessed because of invalid 'file'"
    # Validate ST and YEAR
    if isinstance(ST, str):
        ST = ST.lower()
        if ST in [
            "al",
            "ak",
            "az",
            "ar",
            "ca",
            "co",
            "ct",
            "de",
            "fl",
            "ga",
            "hi",
            "id",
            "il",
            "in",
            "ia",
            "ks",
            "ky",
            "la",
            "me",
            "md",
            "ma",
            "mi",
            "mn",
            "ms",
            "mo",
            "mt",
            "ne",
            "nv",
            "nh",
            "nj",
            "nm",
            "ny",
            "nc",
            "nd",
            "oh",
            "ok",
            "or",
            "pa",
            "ri",
            "sc",
            "sd",
            "tn",
            "tx",
            "ut",
            "vt",
            "va",
            "wa",
            "wv",
            "wi",
            "wy",
            "dc",
        ]:
            ST_message = ""
            if isinstance(YEAR, int):
                if file_message == "":
                    if file in ["od", "wac"]:
                        YEAR_bool = np.any(
                            [
                                np.logical_and(
                                    YEAR in np.arange(2002, 2017), ST == "ak"
                                ),
                                np.logical_and(
                                    YEAR in np.arange(2004, __LODES_YEAR__ + 1),
                                    ST == "az",
                                ),
                                np.logical_and(
                                    YEAR in np.arange(2003, __LODES_YEAR__ + 1),
                                    ST == "ar",
                                ),
                                np.logical_and(
                                    YEAR in np.arange(2010, __LODES_YEAR__ + 1),
                                    ST == "dc",
                                ),
                                np.logical_and(
                                    YEAR in np.arange(2011, __LODES_YEAR__ + 1),
                                    ST == "ma",
                                ),
                                np.logical_and(
                                    YEAR in np.arange(2004, __LODES_YEAR__ + 1),
                                    ST == "ms",
                                ),
                                np.logical_and(
                                    YEAR in np.arange(2003, __LODES_YEAR__ + 1),
                                    ST == "nh",
                                ),
                                np.logical_and(
                                    YEAR in np.arange(2002, __LODES_YEAR__ + 1),
                                    ST
                                    not in ["ak", "az", "ar", "dc", "ma", "ms", "nh"],
                                ),
                            ]
                        )
                        if YEAR_bool == True:
                            YEAR_message = ""
                        else:
                            YEAR_message = f"{YEAR}/{ST} is an invalid 'YEAR'/'ST' input combination"
                    else:
                        if YEAR in np.arange(2002, __LODES_YEAR__ + 1):
                            YEAR_message = ""
                        else:
                            YEAR_message = f"{YEAR} is an invalid 'YEAR' input"
                else:
                    YEAR_message = "'YEAR' cannot be assessed because of invalid 'file'"
            else:
                YEAR_message = f"'YEAR' is {type(YEAR)}, not int"
        else:
            ST_message = f"{ST} is an invalid 'ST' input"
            YEAR_message = "'YEAR' cannot be assessed because of invalid 'ST'"
    else:
        ST_message = f"'ST' is {type(ST)}, not str"
        YEAR_message = "'YEAR' cannot be assessed because of invalid 'ST'"
    # Validate TYPE
    if isinstance(TYPE, str):
        TYPE = TYPE.upper()
        TYPE_bool = TYPE in ["JT00", "JT01", "JT02", "JT03", "JT04", "JT05"]
        if TYPE_bool == True:
            TYPE_message = ""
        else:
            TYPE_message = f"{TYPE} is an invalid 'TYPE' input"
    else:
        TYPE_message = f"'TYPE' is {type(TYPE)}, not str"
    # Organize the error messages
    messages = [
        file_message,
        ST_message,
        PART_message,
        SEG_message,
        TYPE_message,
        YEAR_message,
    ]
    errors = [" ".join(["-->", m]) for m in messages if m != ""]
    # Raise errors, or download
    if len(errors) > 0:
        msg = "\n".join(
            ["The following errors are present in the inputs:", "\n".join(errors)]
        )
        raise ValueError(msg)
    else:
        base_url = f"{__LODES_URL__}{__LODES_VERSION__}/{ST}/{file}"
        if file == "od":
            file_name = f"{ST}_{file}_{PART}_{TYPE}_{YEAR}.csv.gz"
        else:
            file_name = f"{ST}_{file}_{SEG}_{TYPE}_{YEAR}.csv.gz"
        dl_url = f"{base_url}/{file_name}"
        lodes = pd.read_csv(dl_url, compression="gzip")
        return lodes


def dl_xwalk(ST):
    """
    Download the geography crosswalk for Census geographies in a state.
    The crosswalk nests all Census Blocks in larger state geographies.

    Parameters
    ----------
    ST : str
        2-letter postal code for a chosen state; see notes for options and
        definitions. Will be converted to lower-case if not provided as
        such.

    Notes
    -----
    Options for `ST` are:
        1. any of the 50 US states
        2. the District of Columbia (Washington DC)
    US territories, including Puerto Rico and the US Virgin Islands, do not
    have geography crosswalk data available through this source.

    Returns
    -------
    pd.DataFrame
        Geography crosswalk table for `ST`.

    """
    if isinstance(ST, str):
        ST = ST.lower()
        if ST in [
            "al",
            "ak",
            "az",
            "ar",
            "ca",
            "co",
            "ct",
            "de",
            "fl",
            "ga",
            "hi",
            "id",
            "il",
            "in",
            "ia",
            "ks",
            "ky",
            "la",
            "me",
            "md",
            "ma",
            "mi",
            "mn",
            "ms",
            "mo",
            "mt",
            "ne",
            "nv",
            "nh",
            "nj",
            "nm",
            "ny",
            "nc",
            "nd",
            "oh",
            "ok",
            "or",
            "pa",
            "ri",
            "sc",
            "sd",
            "tn",
            "tx",
            "ut",
            "vt",
            "va",
            "wa",
            "wv",
            "wi",
            "wy",
            "dc",
        ]:
            dl_url = f"{__LODES_URL__}{__LODES_VERSION__}/{ST}/{ST}_xwalk.csv.gz"
            xwalk = pd.read_csv(dl_url, compression="gzip")
            return xwalk
        else:
            raise ValueError(f"{ST} is an invalid 'ST' input'")
    else:
        raise TypeError(f"'ST' is {type(ST)}, not str")


if __name__ == "__main__":
    rac = dl_lodes(file="rac", ST="nc", TYPE="JT00", YEAR=2020, SEG="S000", PART="main")

    print(rac)

    wac = dl_lodes(file="wac", ST="nc", TYPE="JT00", YEAR=2020, SEG="S000", PART="main")

    print(wac)

    od = dl_lodes(file="od", ST="nc", TYPE="JT00", YEAR=2020, SEG="S000", PART="main")

    print(od)

    xw = dl_xwalk(ST="nc")
    print(xw)
