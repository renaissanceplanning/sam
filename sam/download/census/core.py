"""
Python-based Census data downloads (replacement for R-based core.py).

Uses censusdis for both TIGER shapefiles and ACS data (unified API).
No R dependencies required.

History:
    - 2026-02-06: Migrated from R (r-tigris, r-tidycensus) to Python (pygris, censusdata)
    - 2026-02-08: Consolidated to censusdis for unified, actively-maintained API

Install dependencies:
    pip install censusdis
"""
import logging
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
import geopandas as gpd

logger = logging.getLogger(__name__)

# Try to import censusdis (unified API for both data and geometry)
try:
    from censusdis import data as ced
    from censusdis import maps as cem
    CENSUSDIS_AVAILABLE = True
except ImportError:
    CENSUSDIS_AVAILABLE = False
    ced = None
    cem = None
    logger.warning("censusdis not available. Install with: pip install censusdis")

from sam.config import CENSUS_API_KEY


def dl_tiger_python(geom: str, **kwargs) -> gpd.GeoDataFrame:
    """
    Download Census TIGER shapefiles using censusdis (Python).

    Replacement for R-based dl_tiger function. Uses censusdis.maps for unified API.

    Args:
        geom: Geography type. Options:
            - 'counties', 'tracts', 'block_groups', 'blocks'
            - 'primary_roads', 'primary_secondary_roads' (not yet supported by censusdis)
            - 'area_water', 'linear_water' (not yet supported by censusdis)
        **kwargs: Common args:
            - state: State FIPS code (2-digit string, e.g., '12')
            - county: County FIPS code (3-digit string, e.g., '057')
            - year: Year (default: 2020)
            - cb: Use cartographic boundary files (default: True for faster downloads)

    Returns:
        GeoDataFrame with TIGER features in EPSG:4269 (NAD83)

    Example:
        >>> # Get Hillsborough County boundary
        >>> counties_gdf = dl_tiger_python('counties', state='12', county='057', year=2022)
        >>>
        >>> # Get block groups in county
        >>> bgs = dl_tiger_python('block_groups', state='12', county='057', year=2022)
    """
    if not CENSUSDIS_AVAILABLE:
        raise ImportError("censusdis is required. Install with: pip install censusdis")

    # Map SAM geometry names to censusdis geography levels
    geom_map = {
        'counties': 'county',
        'tracts': 'tract',
        'block_groups': 'bg',  # censusdis uses 'bg' for block groups
        'blocks': 'block',
        # Roads and water features not yet supported by censusdis maps API
        # May need to keep fallback or wait for censusdis support
    }

    if geom not in geom_map:
        raise ValueError(
            f"'{geom}' is not supported. "
            f"Valid options: {list(geom_map.keys())}"
        )

    geography = geom_map[geom]

    # Extract parameters
    state = kwargs.get('state')
    county = kwargs.get('county')
    year = kwargs.get('year', 2020)

    # Blocks don't have cartographic boundary files - must use full TIGER
    # All other geometries default to CB for faster downloads
    default_cb = True if geography != 'block' else False
    use_cb = kwargs.get('cb', default_cb)

    if not state:
        raise ValueError("'state' parameter is required")

    # Convert 5-digit county codes to 3-digit (last 3 digits)
    if county:
        if isinstance(county, str) and len(county) == 5:
            county = county[-3:]
        elif isinstance(county, list):
            # Handle list of counties - download each separately and concatenate
            gdfs = []
            for c in county:
                c_code = c[-3:] if len(c) == 5 else c
                gdf = _download_single_tiger(geography, state, c_code, year, use_cb)
                gdfs.append(gdf)
            return pd.concat(gdfs, ignore_index=True)

    return _download_single_tiger(geography, state, county, year, use_cb)


def _download_single_tiger(geography: str, state: str, county: Optional[str], year: int, use_cb: bool) -> gpd.GeoDataFrame:
    """
    Download a single TIGER shapefile using censusdis.maps.

    Args:
        geography: censusdis geography type ('county', 'tract', 'bg', 'block')
        state: State FIPS code (2-digit)
        county: County FIPS code (3-digit), optional
        year: Year for shapefiles
        use_cb: Use cartographic boundary files (faster, lower resolution)

    Returns:
        GeoDataFrame with TIGER features
    """
    # Build shapefile scope (state code for state-specific, 'us' for national)
    shapefile_scope = state if state else 'us'

    # Blocks are full TIGER files (large) and need a longer timeout
    timeout = 300 if geography == 'block' else 60

    logger.info(f"Downloading {geography} for state={state}, county={county} with censusdis (year={year}, cb={use_cb})")

    # Create ShapeReader for the year
    reader = cem.ShapeReader(year=year)

    # Download shapefile
    if use_cb:
        # Cartographic boundaries (simpler, good for plotting)
        gdf = reader.read_cb_shapefile(
            shapefile_scope=shapefile_scope,
            geography=geography,
            resolution='500k',  # 500k is default, good balance
            timeout=timeout
        )
    else:
        # Full TIGER files (more detail, larger)
        gdf = reader.read_shapefile(
            shapefile_scope=shapefile_scope,
            geography=geography,
            timeout=timeout
        )

    # Filter by county if specified
    if county and geography in ['tract', 'bg', 'block']:
        # Build expected county FIPS from state + county
        county_fips = f"{state}{county}"

        # Filter to specific county
        # TIGER files have COUNTYFP column for county FIPS
        if 'COUNTYFP' in gdf.columns:
            gdf = gdf[gdf['COUNTYFP'] == county].copy()
        elif 'COUNTY' in gdf.columns:
            gdf = gdf[gdf['COUNTY'] == county].copy()

    # Ensure CRS is EPSG:4269 (NAD83) to match pygris behavior
    if gdf.crs != 'EPSG:4269':
        gdf = gdf.to_crs('EPSG:4269')

    return gdf


def _build_geo_kwargs(geography: str, state: str, county: Optional[str] = None, tract: Optional[str] = None) -> dict:
    """
    Build censusdis geography keyword arguments.

    Helper function to construct kwargs for censusdis.data.download() for different geography types.
    County parameter must be a single string (not a list).

    Args:
        geography: Geography level ('block group', 'tract', 'county', 'state')
        state: State FIPS code (2-digit string)
        county: County FIPS code (3-digit string), optional
        tract: Tract code (string), optional

    Returns:
        Dictionary of kwargs for censusdis.data.download()
    """
    if geography == 'block group':
        return {'state': state, 'county': county, 'block_group': '*'}
    elif geography == 'tract':
        return {'state': state, 'county': county, 'tract': tract if tract else '*'}
    elif geography == 'county':
        return {'state': state, 'county': county if county else '*'}
    elif geography == 'state':
        return {'state': state if state else '*'}
    else:
        raise ValueError(f"Geography '{geography}' not supported")


def _generate_table_variables(table: str, max_vars: int = 50) -> list:
    """
    Generate Census variable codes for a given table.

    Creates variable codes with _E (estimate) suffix for a table.
    Example: 'B01001' → ['B01001_001E', 'B01001_002E', ...]

    Args:
        table: ACS table code (e.g., 'B01001', 'B19001')
        max_vars: Maximum number of variables to generate (default 50)

    Returns:
        List of variable codes with _E suffix

    Notes:
        - Most ACS tables have fewer than 50 variables
        - Using 50 as conservative maximum to avoid requesting too many invalid variables
        - Census API will return only valid variables and ignore invalid ones
        - For tables with more than 50 variables, this will return a subset
    """
    return [f"{table}_{i:03d}E" for i in range(1, max_vars + 1)]


def _transform_censusdis_output(df: pd.DataFrame, geography: str) -> pd.DataFrame:
    """
    Transform censusdis wide-format output to long format matching the
    format expected by sam.acs processing code.

    censusdis returns wide format:
        STATE | COUNTY | TRACT | BLOCK_GROUP | B01001_001E | B01001_002E | ...

    sam.acs expects long format:
        GEOID | variable | estimate

    Where 'variable' contains codes like 'B01001_003' (no E suffix) and
    'estimate' contains the numeric values.

    Args:
        df: DataFrame from censusdis.data.download()
        geography: Geography level for GEOID construction

    Returns:
        Long-format DataFrame with columns: GEOID, variable, estimate
    """
    # Build GEOID from geographic components
    if geography == 'block group':
        df['GEOID'] = (df['STATE'].astype(str).str.zfill(2) +
                      df['COUNTY'].astype(str).str.zfill(3) +
                      df['TRACT'].astype(str).str.zfill(6) +
                      df['BLOCK_GROUP'].astype(str))
    elif geography == 'tract':
        df['GEOID'] = (df['STATE'].astype(str).str.zfill(2) +
                      df['COUNTY'].astype(str).str.zfill(3) +
                      df['TRACT'].astype(str).str.zfill(6))
    elif geography == 'county':
        df['GEOID'] = (df['STATE'].astype(str).str.zfill(2) +
                      df['COUNTY'].astype(str).str.zfill(3))
    elif geography == 'state':
        df['GEOID'] = df['STATE'].astype(str).str.zfill(2)

    # Identify estimate columns (ending in 'E'), excluding geo/metadata columns.
    # censusdis always returns E-suffixed column names (e.g. B01001_002E).
    # Both group_variables and _generate_table_variables produce E-suffixed codes.
    geo_cols = {'STATE', 'COUNTY', 'TRACT', 'BLOCK_GROUP', 'NAME', 'GEOID'}

    import re
    estimate_cols = [col for col in df.columns
                     if col not in geo_cols
                     and re.match(r'^[BC]\d{5}_\d{3}E$', col)]

    if not estimate_cols:
        # Fallback: grab anything ending in 'E' that isn't a geo column
        estimate_cols = [col for col in df.columns
                         if col.endswith('E') and col not in geo_cols]

    if not estimate_cols:
        logger.warning(f"No estimate columns found. Columns: {list(df.columns)}")
        # Last resort: everything that isn't a geo column
        estimate_cols = [col for col in df.columns if col not in geo_cols]

    # Melt wide to long
    df_long = df.melt(
        id_vars=['GEOID'],
        value_vars=estimate_cols,
        var_name='variable',
        value_name='estimate'
    )

    # Strip trailing 'E' suffix: B01001_003E -> B01001_003
    # This matches the variable codes in ACS config DataFrames (no E suffix)
    df_long['variable'] = df_long['variable'].apply(
        lambda v: v[:-1] if v.endswith('E') else v
    )

    return df_long


def dl_census_python(
    survey: str,
    geography: Optional[str] = None,
    variables: Optional[List[str]] = None,
    table: Optional[str] = None,
    year: Optional[int] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Download Census data using censusdis (Python).

    Replacement for R-based dl_census function. Maintains backward compatibility
    with the R version's API.

    Args:
        survey: Survey type - currently only 'acs' is supported (for backward compatibility)
        geography: Geography level ('county', 'tract', 'block group', 'block')
        variables: List of ACS variable codes (e.g., ['B01001_001E', 'B19013_001E'])
        table: ACS table code (e.g., 'B01001'). If provided, downloads all variables from table
        year: ACS year
        state: State FIPS code (2 digits)
        county: County FIPS code (3 or 5 digits)
        **kwargs: Additional arguments

    Returns:
        DataFrame with census data (GEOID as index, variables as columns)

    Example:
        >>> # Get population by block group (matching R API)
        >>> data = dl_census_python(
        ...     'acs',
        ...     geography='block group',
        ...     table='B01001',
        ...     year=2022,
        ...     state='12',
        ...     county='057'
        ... )
    """
    if not CENSUSDIS_AVAILABLE:
        raise ImportError("censusdis is required. Install with: pip install censusdis")

    # Only support ACS for now (matching old R functionality)
    if survey != 'acs':
        raise ValueError(f"Survey '{survey}' not supported. Only 'acs' is currently supported.")

    # Handle county as list or string - if list, process each county separately
    county_list = None
    if county is not None:
        if isinstance(county, list):
            # Convert 5-digit to 3-digit for each county in list
            county_list = [c[-3:] if len(c) == 5 else c for c in county]
            # We'll process this list later by looping
        else:
            # Single county - convert to string
            county = county[-3:] if len(county) == 5 else county

    # Handle table vs variables
    # In R tidycensus, you can specify either 'table' (gets all vars) or 'variables' (specific vars)
    if table is not None and variables is None:
        # censusdis requires individual variable codes with 'E' suffix.
        # Use group_variables (NOT group_leaves) to get ALL variables including
        # subtotals/parents. group_leaves only returns leaf nodes and excludes
        # aggregate variables like B01001_002E (male total) and B01001_026E
        # (female total) that ACS configs depend on.
        import re
        try:
            all_vars = ced.variables.group_variables('acs/acs5', year, table)
            # Filter to estimate variables only (exclude GEO_ID, etc.)
            variables = [v for v in all_vars
                         if re.match(r'^[BC]\d{5}_\d{3}E$', v)]

            if not variables or len(variables) == 0:
                logger.info(f"censusdis returned no estimate variables for {table}. Generating manually.")
                variables = _generate_table_variables(table)
            else:
                logger.info(f"Expanded table {table} to {len(variables)} variables (all levels)")
        except Exception as e:
            logger.warning(f"Could not expand table {table}: {e}. Generating manually.")
            variables = _generate_table_variables(table)

    if variables is None:
        raise ValueError("Either 'variables' or 'table' must be provided")

    if geography is None:
        raise ValueError("'geography' must be provided")

    if year is None:
        raise ValueError("'year' must be provided")

    # Handle multiple counties by looping and concatenating
    if county_list is not None:
        logger.info(f"Downloading ACS {year} data for {len(county_list)} counties in {geography}")
        dfs = []
        for county_str in county_list:
            try:
                # Build geo kwargs for this specific county
                geo_kwargs = _build_geo_kwargs(geography, state, county_str)

                # Download data for this county using censusdis
                df = ced.download('acs/acs5', year, variables, **geo_kwargs)

                # Transform to match censusdata output format (GEOID index)
                df = _transform_censusdis_output(df, geography)
                dfs.append(df)
            except Exception as e:
                logger.error(f"Failed to download data for county {county_str}: {e}")
                # Continue with other counties

        if not dfs:
            raise ValueError("Failed to download data for all counties")

        # Concatenate all DataFrames
        result = pd.concat(dfs, ignore_index=False)
        logger.info(f"Downloaded {len(result)} records across {len(dfs)} counties")
        return result

    # Single county or no county specified
    # Build geography kwargs for censusdis
    if geography in ['block group', 'tract']:
        if not state or not county:
            raise ValueError(f"state and county required for {geography} geography")

    geo_kwargs = _build_geo_kwargs(geography, state, county)

    logger.info(f"Downloading ACS {year} data for {geography}: {variables if not table else f'table {table}'}")

    # Download data using censusdis
    # censusdis uses format: acs/acs5 for 5-year ACS estimates
    df = ced.download('acs/acs5', year, variables, **geo_kwargs)

    # Transform to match expected output format (GEOID index, variable columns)
    return _transform_censusdis_output(df, geography)


# Convenience functions matching SAM's existing API
def dl_acs_python(
    variables: List[str],
    geography: str = 'block group',
    year: int = 2022,
    state: Optional[str] = None,
    county: Optional[str] = None,
    **kwargs
) -> gpd.GeoDataFrame:
    """
    Download ACS data with geometry (combines census data + TIGER shapes).

    Args:
        variables: List of ACS variable codes
        geography: Geography level
        year: ACS year
        state: State FIPS code
        county: County FIPS code

    Returns:
        GeoDataFrame with ACS data and geometry
    """
    # Download census data
    census_df = dl_census_python(
        geography=geography,
        variables=variables,
        year=year,
        state=state,
        county=county,
        **kwargs
    )

    # Download corresponding geometries
    geom_map = {
        'block group': 'block_groups',
        'tract': 'tracts',
        'county': 'counties',
    }

    if geography not in geom_map:
        raise ValueError(f"Geometry not available for geography '{geography}'")

    tiger_kwargs = {'year': year}
    if state:
        tiger_kwargs['state'] = state
    if county and geography in ['block group', 'tract']:
        tiger_kwargs['county'] = county

    geom_gdf = dl_tiger_python(geom_map[geography], **tiger_kwargs)

    # Merge census data with geometry
    # The index of census_df contains GEOIDs
    census_df['GEOID'] = census_df.index.astype(str)

    # Merge
    result = geom_gdf.merge(census_df, on='GEOID', how='inner')

    return result


# Backward compatibility aliases
dl_tiger = dl_tiger_python
dl_census = dl_census_python
dl_acs = dl_acs_python


# =============================================================================
# LODES (Longitudinal Employer-Household Dynamics) Functions
# These functions don't use R - they download directly from Census FTP
# =============================================================================

# LODES constants
__LODES_YEAR__ = 2022
__LODES_VERSION__ = 8
__LODES_URL__ = "https://lehd.ces.census.gov/data/lodes/LODES"


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
