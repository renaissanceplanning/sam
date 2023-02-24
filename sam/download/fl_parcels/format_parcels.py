# -*- coding: utf-8 -*-
"""
Created on Thu Jan  7 10:54:07 2021

@author: Aaron Weinstock
"""

# TODO: set up a default field specs dictionary for dl_parcel_nal that
# covers all variables, and set it as the default for the function

# %% Imports

import numpy as np
import geopandas as gpd
import pandas as pd
from scipy import stats
import os
import tempfile
import shutil
import urllib
import zipfile
import pyproj
from shapely.validation import make_valid


# Helper Functions
def validate_directory(path_or_directory):
    """
    check for the existence of a directory or the directory in a path, and
    attempt to create it if it doesn't exist

    Parameters
    ----------
    path_or_directory : str
        local path or directory

    Returns
    -------
    str
        a normalized version of the input path or directory

    Raises
    ------
    ValueError
        if the directory doesn't exist and cannot be created
    """

    # Normalize the path and extract the directory
    pod = os.path.normpath(path_or_directory)
    ext = os.path.splitext(pod)[1]
    if ext == "":
        save_directory = pod
    else:
        save_directory = os.path.dirname(pod)

    # If the save directory doesn't exist, try to create it
    if os.path.exists(save_directory):
        pass
    else:
        # Split the save directory into it's component parts
        main_dir = save_directory
        sub_dir = None
        folders = []
        while sub_dir != "":
            main_dir, sub_dir = os.path.split(main_dir)
            folders.append(sub_dir)
        folders = folders[:-1]
        folders.reverse()

        # Check existence or try to create iteratively
        while main_dir != save_directory:
            main_dir = os.path.join(main_dir, folders[0])
            folders = folders[1:]
            if not os.path.exists(main_dir):
                try:
                    os.mkdir(main_dir)
                except:
                    message = " ".join(
                        [
                            "directory does not exist",
                            "and cannot be created;",
                            "failed trying to create:",
                            main_dir,
                        ]
                    )
                    raise ValueError(message)

    # If we made it through the above, the path or directory now exists/is
    # valid, so return it. otherwise, an error would have been hit, so we
    # wouldn't get to the return anyway
    return pod


# %% Functions


def dl_parcel_gis(gis_url, crs):
    """
    downloads the FDOR parcel GIS data for a county from an FDOR FTP map data
    subfolder

    Parameters
    ----------
    gis_url : str
        url to an FDOR FTP GIS file
    crs : pyroj CRS object
        CRS to which to transform the GIS data

    Returns
    -------
    geopandas GeoDataFrame of FDOR parcel boundaries for the county
    """

    # load from the url
    # -----------------
    print("----> downloading the shape")

    gdf = gpd.read_file(gis_url)
    gdf = gdf.astype({"PARCELNO": str})

    # Repair Geometries
    gdf["geometry"] = gdf.apply(
        lambda row: make_valid(row.geometry)
        if not row.geometry.is_valid
        else row.geometry,
        axis=1,
    )

    # dissolve on id
    # --------------
    print("----> dissolving on parcel ID")

    if len(np.unique(gdf.PARCELNO)) < len(gdf.index):
        gdf = gdf.dissolve(by="PARCELNO").reset_index()

    # reprojecting
    # ------------
    print("----> reprojecting")

    gdf = gdf.to_crs(crs)

    # done
    # ----
    return gdf


# ----------------------------------------------------------------------------


def dl_parcel_nal(nal_url, field_specs={}):
    """
    downloads the FDOR parcel NAL data for a county from an FDOR FTP tax roll
    data subfolder

    Parameters
    ----------
    nal_url : str
        url to an FDOR FTP NAL file
    fields_specs : dict
        dictionary with the following format:
            {variable: spec_dict}, where 'variable' is a variable from NAL to
            keep and 'spec_dict' is a dict of the specs used to load and
            format the variable. 'spec_dict' has the following keys:
                dtype: type for this variable (e.g., int, str)
                rename: name to rename variable
                na_value: value used to fill NA (should be same type specified
                in dtype if dtype is given)
                min_value: minimum acceptable value for the field (should be
                same type specified in dtype if dtype is given)
                aggfunc: function used to aggregate this variable over the
                same ID (e.g., sum, mean)
        Default `{}`, pandas defaults will be used for dtype, no renaming or
        NA filling will be completed, and aggfunc will be "sum" for numerics
        or "mode" for objects

    Notes
    -----
    for each variable, as many keys as are relevant can and should be
    specified. If you only want to provide the variable with no other info,
    set the value for that key to an empty dict. Users should fill out as many
    options in this parameter as possible; leaving as the default `{}` is
    highly discouraged (due to data size and complexity)

    Returns
    -------
    pandas DataFrame of FDOR parcel NAL data for the county
    """

    # load from the url
    # -----------------
    print("----> downloading the table")

    # Try to read it directly from web. If it doesn't go, download it,
    # and load it from the zip
    # (Note: urllib is used bc requests doesn't work with FTP sites)
    # (https://stackoverflow.com/questions/11768214/python-download-a-file-from-an-ftp-server)
    try:
        df = gpd.read_file(nal_url)
    except:
        td = tempfile.mkdtemp()
        fp = os.path.join(td, os.path.basename(nal_url))
        with urllib.request.urlopen(nal_url) as r:
            with open(fp, "wb") as f:
                shutil.copyfileobj(r, f)
        with zipfile.ZipFile(fp) as z:
            load_file = z.namelist()[0]
        load_path = "".join(["zip://", fp, "!", load_file])
        df = gpd.read_file(load_path)
        shutil.rmtree(td)

    df = pd.DataFrame(df.drop(columns="geometry"))
    if field_specs != {}:
        if "NO_RES_UNT" in list(field_specs.keys()):
            if "NO_RES_UNTS" in list(df.columns):
                df.rename(columns={"NO_RES_UNTS":"NO_RES_UNT"}, inplace=True)
        
        if "TOT_LVG_AR" in list(field_specs.keys()):
            if "TOT_LVG_AREA" in list(df.columns):
                df.rename(columns={"TOT_LVG_AREA":"TOT_LVG_AR"}, inplace=True)
        
        cols = np.unique(["PARCEL_ID"] + list(field_specs.keys())).tolist()
        df = df[cols]

    # filling na
    # ----------
    print("----> filling NA")

    # extract what we're filling
    fna = {}
    df = df.replace("", pd.NA)
    for key in field_specs.keys():
        if "na_value" in field_specs[key].keys():
            fna[key] = field_specs[key]["na_value"]

    # fill (and cover PARCELNO manually just to be safe)
    df = df.fillna(value=fna)
    df = df.fillna(value={"PARCEL_ID": "unknown"})

    # setting floor
    # -------------
    print("----> setting floor")

    # truncate in loop
    for key in field_specs.keys():
        if "min_value" in field_specs[key].keys():
            df.loc[:, key] = df[key].clip(lower=0)

    # data types
    # ----------
    print("----> setting data types")

    # extract what we're resetting
    fdt = {}
    for key in field_specs.keys():
        if "dtype" in field_specs[key].keys():
            fdt[key] = field_specs[key]["dtype"]

    # reset dtype (and cover PARCELNO manually just to be safe)
    df = df.astype(fdt)
    df = df.astype({"PARCEL_ID": str})

    # aggregating
    # -----------

    if len(np.unique(df.PARCEL_ID)) < len(df.index):
        print("----> aggregating to parcel ID")

        # extract how we're aggregating
        faggr = {}
        for key in field_specs.keys():
            if "aggfunc" in field_specs[key].keys():
                faggr[key] = field_specs[key]["aggfunc"]

        # if there's any aggfuncs missing, add them in
        agg_miss = [
            c for c in df.columns.tolist() if c not in ["PARCELNO"] + list(faggr.keys())
        ]
        if agg_miss == []:
            dfdt = df.dtypes
            for c in agg_miss:
                if dfdt[c] == "object":
                    agg_miss[c] = stats.mode
                else:
                    agg_miss[c] = sum

        # aggregate
        df = df.groupby("PARCELNO").agg(faggr).reset_index()

        # modes are returned weirdly, so extract value
        mode_cols = [key for key, value in faggr.items() if value == stats.mode]
        for c in mode_cols:
            df[c] = [x[0][0] for x in df[c]]

    # rename
    # ------
    print("----> renaming")

    # extract what we're renaming
    frename = {}
    for key in field_specs.keys():
        if "rename" in field_specs[key].keys():
            frename[key] = field_specs[key]["rename"]

    # rename (and cover PARCELNO manually just to be safe)
    df = df.rename(columns=frename)
    df = df.rename(columns={"PARCEL_ID": "PARCELNO"})

    # done
    # ----
    return df

# ----------------------------------------------------------------------------


def dl_parcel_nal_csv(nal_url, field_specs):
    """
    based on

    Parameters
    ----------
    nal_url : str
        url to an FDOR FTP NAL file
    fields_specs : dict
        dictionary with the following format:
            {variable: spec_dict}, where 'variable' is a variable from NAL to
            keep and 'spec_dict' is a dict of the specs used to load and
            format the variable. 'spec_dict' has the following keys:
                dtype: type for this variable (e.g., int, str)
                rename: name to rename variable
                na_value: value used to fill NA (should be same type specified
                in dtype if dtype is given)
                min_value: minimum acceptable value for the field (should be
                same type specified in dtype if dtype is given)
                aggfunc: function used to aggregate this variable over the
                same ID (e.g., sum, mean)
        Must be set as this version of the function is for dtype issues with 
        certain csvs

    Notes
    -----
    for each variable, as many keys as are relevant can and should be
    specified. If you only want to provide the variable with no other info,
    set the value for that key to an empty dict. Users should fill out as many
    options in this parameter as possible; leaving as the default `{}` is
    highly discouraged (due to data size and complexity)

    Returns
    -------
    pandas DataFrame of FDOR parcel NAL data for the county
    """

    # load from the url
    # -----------------
    print("----> downloading the table")

    # Try to read it directly from web. If it doesn't go, download it,
    # and load it from the zip
    # (Note: urllib is used bc requests doesn't work with FTP sites)
    # (https://stackoverflow.com/questions/11768214/python-download-a-file-from-an-ftp-server)
    
    #handle the common renamed columns
    # csv_field = field_specs.copy()
    
    # if "NO_RES_UNT" in list(field_specs.keys()):
    #     csv_field["NO_RES_UNTS"] = csv_field.pop("NO_RES_UNT")
        
    # if "TOT_LVG_AR" in list(field_specs.keys()):
    #     csv_field["TOT_LVG_AREA"] = csv_field.pop("TOT_LVG_AR")
    
    
    # try:
    #     df = pd.read_csv(nal_url,
    #                      usecols=csv_field.keys(),
    #                      dtype={key:csv_field[key]['dtype'] 
    #                             for key in csv_field.keys()})
        
    try:
        df = pd.read_csv(nal_url,
                         usecols=field_specs.keys(),
                         dtype={key:field_specs[key]['dtype'] 
                                for key in field_specs.keys()})
        
    except:
        td = tempfile.mkdtemp()
        fp = os.path.join(td, os.path.basename(nal_url))
        with urllib.request.urlopen(nal_url) as r:
            with open(fp, "wb") as f:
                shutil.copyfileobj(r, f)
        with zipfile.ZipFile(fp) as z:
            load_file = z.namelist()[0]
        load_path = "".join(["zip://", fp, "!", load_file])
        df = df = pd.read_csv(nal_url,
                         usecols=field_specs.keys(),
                         dtype={key:field_specs[key]['dtype'] 
                                for key in field_specs.keys()})
        shutil.rmtree(td)

    # df = pd.DataFrame(df.drop(columns="geometry"))
    if field_specs != {}:
        if "NO_RES_UNT" in list(field_specs.keys()):
            if "NO_RES_UNTS" in list(df.columns):
                df.rename(columns={"NO_RES_UNTS":"NO_RES_UNT"}, inplace=True)
        
        if "TOT_LVG_AR" in list(field_specs.keys()):
            if "TOT_LVG_AREA" in list(df.columns):
                df.rename(columns={"TOT_LVG_AREA":"TOT_LVG_AR"}, inplace=True)
        
        cols = np.unique(["PARCEL_ID"] + list(field_specs.keys())).tolist()
        df = df[cols]

    # filling na
    # ----------
    print("----> filling NA")

    # extract what we're filling
    fna = {}
    df = df.replace("", pd.NA)
    for key in field_specs.keys():
        if "na_value" in field_specs[key].keys():
            fna[key] = field_specs[key]["na_value"]

    # fill (and cover PARCELNO manually just to be safe)
    df = df.fillna(value=fna)
    df = df.fillna(value={"PARCEL_ID": "unknown"})

    # setting floor
    # -------------
    print("----> setting floor")

    # truncate in loop
    for key in field_specs.keys():
        if "min_value" in field_specs[key].keys():
            df.loc[:, key] = df[key].clip(lower=0)

    # data types
    # ----------
    print("----> setting data types")

    # extract what we're resetting
    fdt = {}
    for key in field_specs.keys():
        if "dtype" in field_specs[key].keys():
            fdt[key] = field_specs[key]["dtype"]

    # reset dtype (and cover PARCELNO manually just to be safe)
    df = df.astype(fdt)
    df = df.astype({"PARCEL_ID": str})

    # aggregating
    # -----------

    if len(np.unique(df.PARCEL_ID)) < len(df.index):
        print("----> aggregating to parcel ID")

        # extract how we're aggregating
        faggr = {}
        for key in field_specs.keys():
            if "aggfunc" in field_specs[key].keys():
                faggr[key] = field_specs[key]["aggfunc"]

        # if there's any aggfuncs missing, add them in
        agg_miss = [
            c for c in df.columns.tolist() if c not in ["PARCELNO"] + list(faggr.keys())
        ]
        if agg_miss == []:
            dfdt = df.dtypes
            for c in agg_miss:
                if dfdt[c] == "object":
                    agg_miss[c] = stats.mode
                else:
                    agg_miss[c] = sum

        # aggregate
        df = df.groupby("PARCELNO").agg(faggr).reset_index()

        # modes are returned weirdly, so extract value
        mode_cols = [key for key, value in faggr.items() if value == stats.mode]
        for c in mode_cols:
            df[c] = [x[0][0] for x in df[c]]

    # rename
    # ------
    print("----> renaming")

    # extract what we're renaming
    frename = {}
    for key in field_specs.keys():
        if "rename" in field_specs[key].keys():
            frename[key] = field_specs[key]["rename"]

    # rename (and cover PARCELNO manually just to be safe)
    df = df.rename(columns=frename)
    df = df.rename(columns={"PARCEL_ID": "PARCELNO"})

    # done
    # ----
    return df

# ----------------------------------------------------------------------------


def merge_parcels(gis_gdf, nal_df):
    """
    merge parcel NAL data to GIS data, and optionally save to shape

    Parameters
    ----------
    gis_gdf : geopandas GeoDataFrame
        geodataframe of parcel boundaries, with id field "PARCELNO"; this is
        the result of `dl_parcel_gis`
    nal_df : pandas DataFrame
        dataframe of parcel NAL data, with id field "PARCELNO"; this is
        the result of `dl_parcel_nal`
    save_path : str, optional
        path to save the result. The default is None, no save will be
        performed

    Returns
    -------
    dict of format:
        result: geodataframe of merged GIS/NAL data
        gis_total: number of records in the GIS file
        nal_total: number of records in the NAL file
        result_total: number of records in the merged GIS/NAL results
        save_path: save path to the merged result (if provided)
    """

    # merge
    # -----
    print("----> merging shape and table")

    # Use a dict to organize the information for the return
    rd = {
        "result": pd.merge(
            gis_gdf, nal_df, left_on="PARCELNO", right_on="PARCELNO", how="inner"
        ),
        "gis_total": len(gis_gdf.index),
        "nal_total": len(nal_df.index),
    }
    rd["result_total"] = len(rd["result"].index)

    # done
    # ----
    return rd


# ----------------------------------------------------------------------------


def process_parcels(gis_url, nal_url, transform_crs, field_specs={}):
    """
    downloads a publicly-available parcel boundaries from FDOR FTP data
    archives, attributes it with NAL data for that year, and save locally as
    a shapefile

    Parameters
    ----------
    year : int
        year for which to pull data
    county : str
        name of a county in Florida
    crs : str, geopandas GeoDataFrame, or anything accepted by
    `pyproj.CRS.from_user_input`
        an object from which the desired transform can be inferred; includes
        a path to a shapefile, a GeoDataFrame, or some user input defining
        the CRS. see Notes for details
    save_path : str
        path to save the result
    fields_specs : dict
        dictionary with the following format:
            {variable: spec_dict}, where 'variable' is a variable from NAL to
            keep and 'spec_dict' is a dict of the specs used to load and
            format the variable. 'spec_dict' has the following keys:
                dtype: type for this variable (e.g., int, str)
                rename: name to rename variable
                na_value: value used to fill NA (should be same type specified
                in dtype if dtype is given)
                aggfunc: function used to aggregate this variable over the
                same ID (e.g., sum, mean)
        Default `{}`, pandas defaults will be used for dtype, no renaming or
        NA filling will be completed, and aggfunc will be "sum" for numerics
        or "mode" for objects

    Notes
    -----
    `pyproj.CRS.from_user_input` can take:
        - PROJ JSON string
        - PROJ JSON dict
        - WKT string
        - An authority string
        - An EPSG integer code
        - A tuple of (“auth_name”: “auth_code”)
        - An object with a to_json method
    Any of these would be valid inputs to the `transform_crs` parameter

    for each variable in `field_specs`, as many keys as are relevant can and
    should be specified. If you only want to provide the variable with no
    other info set the value for that key to an empty dict. Users should fill
    out as many options in this parameter as possible; leaving as the default
    `{}` is highly discouraged (due to data size and complexity)

    Returns
    -------
    dict of format:
        result: geodataframe of merged GIS/NAL data
        gis_total: number of records in the GIS file
        nal_total: number of records in the NAL file
        result_total: number of records in the merged GIS/NAL results
        save_path: save path to the merged result (if provided)
    """

    # validation of inputs
    # --------------------

    # crs
    print("Validating transform CRS")
    crs = pyproj.CRS.from_user_input(transform_crs)

    # 1. gis
    # ------
    print("1. Downloading parcel GIS data")

    gis = dl_parcel_gis(gis_url=gis_url, crs=crs)

    # 2. nal
    # ------
    print("2. Downloading parcel NAL data")

    nal = dl_parcel_nal(nal_url=nal_url, field_specs=field_specs)

    # 3. save
    # -------
    print("3. Merging and saving")

    save_info = merge_parcels(gis_gdf=gis, nal_df=nal)

    # done
    # ----
    print("Done!")
    print("")
    return save_info

# ----------------------------------------------------------------------------


def process_parcels_csv(gis_url, nal_url, transform_crs, field_specs):
    """
    downloads a publicly-available parcel boundaries from FDOR FTP data
    archives, attributes it with NAL data for that year, and save locally as
    a shapefile
    
    designed when only csv is avaliable and requires a field spec to read the csv

    Parameters
    ----------
    year : int
        year for which to pull data
    county : str
        name of a county in Florida
    crs : str, geopandas GeoDataFrame, or anything accepted by
    `pyproj.CRS.from_user_input`
        an object from which the desired transform can be inferred; includes
        a path to a shapefile, a GeoDataFrame, or some user input defining
        the CRS. see Notes for details
    save_path : str
        path to save the result
    fields_specs : dict
        dictionary with the following format:
            {variable: spec_dict}, where 'variable' is a variable from NAL to
            keep and 'spec_dict' is a dict of the specs used to load and
            format the variable. 'spec_dict' has the following keys:
                dtype: type for this variable (e.g., int, str)
                rename: name to rename variable
                na_value: value used to fill NA (should be same type specified
                in dtype if dtype is given)
                aggfunc: function used to aggregate this variable over the
                same ID (e.g., sum, mean)
        Default `{}`, pandas defaults will be used for dtype, no renaming or
        NA filling will be completed, and aggfunc will be "sum" for numerics
        or "mode" for objects

    Notes
    -----
    `pyproj.CRS.from_user_input` can take:
        - PROJ JSON string
        - PROJ JSON dict
        - WKT string
        - An authority string
        - An EPSG integer code
        - A tuple of (“auth_name”: “auth_code”)
        - An object with a to_json method
    Any of these would be valid inputs to the `transform_crs` parameter

    for each variable in `field_specs`, as many keys as are relevant can and
    should be specified. If you only want to provide the variable with no
    other info set the value for that key to an empty dict. Users should fill
    out as many options in this parameter as possible; leaving as the default
    `{}` is highly discouraged (due to data size and complexity)

    Returns
    -------
    dict of format:
        result: geodataframe of merged GIS/NAL data
        gis_total: number of records in the GIS file
        nal_total: number of records in the NAL file
        result_total: number of records in the merged GIS/NAL results
        save_path: save path to the merged result (if provided)
    """

    # validation of inputs
    # --------------------

    # crs
    print("Validating transform CRS")
    crs = pyproj.CRS.from_user_input(transform_crs)

    # 1. gis
    # ------
    print("1. Downloading parcel GIS data")

    gis = dl_parcel_gis(gis_url=gis_url, crs=crs)

    # 2. nal
    # ------
    print("2. Downloading parcel NAL data")

    nal = dl_parcel_nal_csv(nal_url=nal_url, field_specs=field_specs)

    # 3. save
    # -------
    print("3. Merging and saving")

    save_info = merge_parcels(gis_gdf=gis, nal_df=nal)

    # done
    # ----
    print("Done!")
    print("")
    return save_info