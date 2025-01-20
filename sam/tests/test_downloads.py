# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 14:30:54 2022

@author: AZ7
"""
# todo clean up tests for automatic testing

import os
import rputils
import numpy as np
from sam import acs
from sam.lodes import lodes
from sam.download.census import dl_tiger, dl_census, dl_xwalk, dl_lodes

from sam.osm import OSMNetwork
from sam.download.sld import dl_sld
from sam.config import TEST_AOI
from sam.download.ms_footprints import dl_ms_building_footprints
from sam.parcels import download_fl_parcels

# script pathing
__script_path__ = os.path.dirname(__file__)

# import pytest
TEST_CRS = rputils.create_crs(crs_input=2881)
TEST_STATE = "FL"
TEST_COUNTY = ["12086"]
TEST_COUNTY_NM = "Miami-Dade"
TEST_YEAR = 2019
AOI = TEST_AOI


# Residence area characteristics
def test_dl_rac():
    rac = lodes.rac(state=TEST_STATE, year=TEST_YEAR)
    rac["ctyfips"] = [x[:5] for x in rac.h_geocode]
    rac = rac[rac.ctyfips.isin(TEST_COUNTY)]
    return rac.drop(columns="ctyfips")


# def test_rac(df=test_dl_rac()):
# 	is_df = isinstance(df, pd.DataFrame)
# 	non_zero = len(df) > 0
# 	assert is_df + non_zero == 2
#
#
# # Workplace area characteristics
def test_dl_wac():
    wac = lodes.wac(state=TEST_STATE, year=TEST_YEAR)
    wac["ctyfips"] = [x[:5] for x in wac.w_geocode]
    wac = wac[wac.ctyfips.isin(TEST_COUNTY)]
    return wac.drop(columns="ctyfips")


# def test_wac(df=test_dl_wac()):
# 	is_df = isinstance(df, pd.DataFrame)
# 	non_zero = len(df) > 0
# 	assert is_df + non_zero == 2
#
#
# Origin-destination jobs
def test_dl_lodes():
    od = lodes.od(state=TEST_STATE, year=TEST_YEAR)
    od["h_ctyfips"] = [x[:5] for x in od.h_geocode]
    od["w_ctyfips"] = [x[:5] for x in od.w_geocode]
    od = od[
        np.logical_or(od.h_ctyfips.isin(TEST_COUNTY), od.w_ctyfips.isin(TEST_COUNTY))
    ]
    return od.drop(columns=["h_ctyfips", "w_ctyfips"])


# def test_od(df=test_dl_lodes()):
# 	is_df = isinstance(df, pd.DataFrame)
# 	non_zero = len(df) > 0
# 	assert is_df + non_zero == 2
#
#
# # Geography crosswalk
def test_dl_xwalk():
    return lodes.xwalk(state=TEST_STATE)


# def test_od(df=test_dl_xwalk()):
# 	is_df = isinstance(df, pd.DataFrame)
# 	non_zero = len(df) > 0
# 	assert is_df + non_zero == 2
#
#
def test_dl_sld():
    # download sld data in AOI
    return dl_sld(mask=AOI)


# def test_sld(df=test_dl_sld()):
# 	is_df = isinstance(df, pd.DataFrame)
# 	non_zero = len(df) > 0
# 	assert is_df + non_zero == 2


# Building Footprints
def test_dl_buildings():
    # Download buildings within that AOI
    return dl_ms_building_footprints(state=TEST_STATE, mask=AOI)


# # Jobs files aggregated to block group
def test_aggregate_census():
    rac = test_dl_rac()
    wac = test_dl_wac()
    od = test_dl_lodes()
    xw = test_dl_xwalk()
    rac_bg = rac.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)
    wac_bg = wac.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)
    od_bg = od.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)

    def test_agg():
        assert len(rac_bg) == len(
            xw.loc[xw.tabblk2010.isin(rac.h_geocode.astype(np.int64))].bgrp.unique()
        )

    test_agg()
    return rac_bg, wac_bg, od_bg


# Census geographies in Miami-Dade County Florida
def test_dl_census_geos():
    kwargs = {"state": TEST_STATE, "county": TEST_COUNTY[0], "year": TEST_YEAR}
    blk = dl_tiger(
        geom="blocks",
        **kwargs,
    )
    bg = dl_tiger(
        geom="block_groups",
        **kwargs,
    )
    tract = dl_tiger(
        geom="tracts",
        **kwargs,
    )
    counties = dl_tiger(
        geom="counties", kwargs={"state": TEST_STATE, "year": TEST_YEAR}
    )
    return blk, bg, tract, counties


def test_dl_osm_network():
    # read in AOI and project to test crs, then inward buffer 15 miles
    AOI = TEST_AOI.to_crs(TEST_CRS)
    AOI = AOI.buffer(distance=--79200)
    walk = OSMNetwork.walk(geometry=AOI, crs=TEST_CRS)
    drive = OSMNetwork.drive(geometry=AOI, crs=TEST_CRS)
    bike = OSMNetwork.bike(geometry=AOI, crs=TEST_CRS)
    return walk, drive, bike


def test_dl_fl_par():
    return download_fl_parcels(
        county=TEST_COUNTY_NM,
        crs=TEST_CRS,
        year=TEST_YEAR,
    )


# test acs variables
def test_dl_acs():
    sex = acs.sex(state=TEST_STATE, year=TEST_YEAR, county=TEST_COUNTY_NM)
    hh_inc = acs.hh_income(state=TEST_STATE, year=TEST_YEAR, county=TEST_COUNTY_NM)
    age = acs.age(state=TEST_STATE, year=TEST_YEAR, county=TEST_COUNTY_NM)
    poverty = acs.ratio_of_income_to_poverty_level(
        state=TEST_STATE, year=TEST_YEAR, county=TEST_COUNTY_NM
    )
    hh_veh = acs.hh_vehicles(state=TEST_STATE, year=TEST_YEAR, county=TEST_COUNTY_NM)
    tenure = acs.tenure(state=TEST_STATE, year=TEST_YEAR, county=TEST_COUNTY_NM)


if __name__ == "__main__":
    # test rac
    # rac_df = test_dl_rac()
    # print(rac_df.head())

    # # test wac
    # wac_df = test_dl_wac()
    # print(wac_df.head())

    # # test lodes
    # lodes_df = test_dl_lodes()
    # print(lodes_df.head())

    # # test xwalk
    # xwalk_df = test_dl_xwalk()
    # print(xwalk_df.head())

    # # test aggregation
    # rac_bg, wac_bg, od_bg = test_aggregate_census()
    # print(rac_bg.head())
    # print(wac_bg.head())
    # print(od_bg.head())

    # # test sld
    # sld_df = test_dl_sld()
    # print(sld_df.head())

    # test parcel dl
    par_df = test_dl_fl_par()
    print(par_df.head())

    # test osm downloads
    walk, drive, bike = test_dl_osm_network()
    print(walk.head())
    print(drive.head())
    print(bike.head())

    # test building footprints
    bld_df = test_dl_buildings()
    print(bld_df.head())
    print()

    # TODO: confirm osm, parcel downloader, and aggregation work
