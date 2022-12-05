# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 10:01:19 2022

@author: Aaron Weinstock
"""

# %% Imports and globals

import geopandas as gpd
import pandas as pd

# %% Functions

def dl_ms_building_footprints(state, **kwargs):
    '''
    Download the Microsoft US Buildings Footprints polygons for a state.

    Parameters
    ----------
    state : str
        Either the name, USPS code, or FIPS number for a state.
    **kwargs :
        Passed to `gpd.read_file()`.
        
    Notes
    -----    
    File sizes vary by state, and many approach or are greater than 1 GB in 
    size! If you're downloading for an entire state, please be patient.
    If you only need building footprints in a smaller subregion, the `mask`
    or `bbox` kwargs of `gpd.read_file()` may be of use. The GitHub for the 
    Microsoft US Buildings Footprints project indicates file sizes by state,
    for reference.
    
    See Also
    --------
    - GitHub for Microsoft US Buildings Footprints:
        "https://github.com/microsoft/USBuildingFootprints"
    - `gpd.read_file()` documentation:
        https://geopandas.org/en/stable/docs/reference/api/geopandas.read_file.html

    Returns
    -------
    gdf : gpd.GeoDataFrame
        Polygons of building footprints in `state` (in EPSG:4326).

    '''
    # States by name, usps, and fips
    STATE_DF = pd.DataFrame([
        ("Alabama", "AL", "01"), 
        ("Alaska", "AK", "02"),
        ("Arizona", "AZ", "04"), 
        ("Arkansas", "AR", "05"),
        ("California", "CA", "06"), 
        ("Colorado", "CO", "08"),
        ("Connecticut", "CT", "09"), 
        ("Delaware", "DE", "10"),
        ("District of Columbia", "DC", "11"),
        ("Florida", "FL", "12"), 
        ("Georgia", "GA", "13"),
        ("Hawaii", "HI", "15"), 
        ("Idaho", "ID", "16"),
        ("Illinois", "IL", "17"), 
        ("Indiana", "IN", "18"),
        ("Iowa", "IA", "19"), 
        ("Kansas", "KS", "20"),
        ("Kentucky", "KY", "21"), 
        ("Louisiana", "LA", "22"),
        ("Maine", "ME", "23"), 
        ("Maryland", "MD", "24"),
        ("Massachusetts", "MA", "25"),
        ("Michigan", "MI", "26"), 
        ("Minnesota", "MN", "27"),
        ("Mississippi", "MS", "28"), 
        ("Missouri", "MO", "29"),
        ("Montana", "MT", "30"),
        ("Nebraska", "NE", "31"), 
        ("Nevada", "NV", "32"),
        ("New Hampshire", "NH", "33"),
        ("New Jersey", "NJ", "34"), 
        ("New Mexico", "NM", "35"),
        ("New York", "NY", "36"),
        ("North Carolina", "NC", "37"),
        ("North Dakota", "ND", "38"), 
        ("Ohio", "OH", "39"),
        ("Oklahoma", "OK", "40"), 
        ("Oregon", "OR", "41"),
        ("Pennsylvania", "PA", "42"),
        ("Rhode Island", "RI", "44"),
        ("South Carolina", "SC", "45"),
        ("South Dakota", "SD", "46"),
        ("Tennessee", "TN", "47"), 
        ("Texas", "TX", "48"),
        ("Utah", "UT", "49"), 
        ("Vermont", "VT", "50"),
        ("Virginia", "VA", "51"),
        ("Washington", "WA", "53"),
        ("West Virginia", "WV", "54"),
        ("Wisconsin", "WI", "55"), 
        ("Wyoming", "WY", "56")
    ], columns=["name","usps","fips"]
    )
    # Grab the appropriate row for the state using the given expression
    if isinstance(state, str):
        # State is properly typed
        if len(state) == 2:
            # It's either a USPS code or a FIPS number
            if state.isdigit() == True:
                # It's a FIPS number
                state_rep = state
                row = STATE_DF[STATE_DF.fips == state_rep]
            else:
                # It's a USPS code
                state_rep = state.upper()
                row = STATE_DF[STATE_DF.usps == state_rep]
        else:
            # It's a state name
            state_rep = state.replace(".","").title().replace("Of","of")
            if state_rep == "Washington Dc":
                state_rep = "District of Columbia"
            row = STATE_DF[STATE_DF.name == state_rep]
    else:
        # State is NOT properly typed
        raise TypeError(f"Expected str for 'state', got {type(state)}")
    # Grab the state name and format it to match the MSBF expression
    if len(row) == 1:
        # You found a state :)
        state_msbf = row.name.iloc[0].replace(" ","")
    else:
        # You didn't find a state :(
        raise ValueError(f"{state} is not a valid state name, USPS code, or "\
                         "FIPS number")
    # Set the download URL using the formatted state name
    URL_BASE = "https://usbuildingdata.blob.core.windows.net/usbuildings-v2"
    file = f"{state_msbf}.geojson.zip"
    url = f"{URL_BASE}/{file}"
    # Download the shape and return
    gdf = gpd.read_file(url, **kwargs)
    return gdf

def focal_area_for_latest_release():
    '''
    Download the focal area for the latest release of Microsoft US Buildings
    Footprints.
    
    Notes
    -----
    From the GitHub for Microsoft US Buildings Footprints (Dec 5, 2022):
        "Footprints inside the highlighted region on the map are from 
        2019-2020. There are 73,250,745 such building footprints. This is the 
        focal area where we rerun extraction for the latest release. The rest 
        of the footprints were extracted from older images, having wider range 
        of capture dates, averaging 2012 year approximately. We have reused 
        footprints from previous releases in this area."
        
    See Also
    --------
    GitHub for Microsoft US Buildings Footprints:
        "https://github.com/microsoft/USBuildingFootprints"

    Returns
    -------
    faflr : TYPE
        Polygons for the focal area for the latest release (in EPSG:4326).

    '''
    URL_BASE = "https://usbuildingdata.blob.core.windows.net/usbuildings-v2"
    file = "US_areas_L13.geojson"
    url = f"{URL_BASE}/{file}"
    faflr = gpd.read_file(url)
    return faflr
    
# TODO: better CRS? 5070 covers ~continental~ US, but we may want more
# comprehensive support for AK and HI
def isin_focal_area(gdf):
    '''
    Check how much of a region lies within the focal area for the latest 
    release of Microsoft US Buildings Footprints.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        A region of interest.
        
    Notes
    -----
    The intersection operation to calculate the percentage of the region within
    the focal area will be costly for complex polygons; please be patient if
    you region of interest is complex, or try to simplify its representation.

    Returns
    -------
    pct : float
        Percent of the area of `gdf` in the focal region.

    '''
    gdf_proj = gdf[["geometry"]].to_crs(5070)
    faflr_proj = focal_area_for_latest_release().to_crs(5070)
    itsn = gpd.overlay(gdf_proj, faflr_proj, how="intersection")
    pct = itsn.geometry.area.sum() / gdf_proj.geometry.area.sum()
    return pct

