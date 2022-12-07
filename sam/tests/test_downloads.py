# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 14:30:54 2022

@author: AZ7
"""
# todo clean up tests for automatic testing

import os
import rputils
import numpy as np
import pandas as pd
from sam.lodes import lodes
from sam.download.census import dl_tiger, dl_census, dl_xwalk, dl_lodes
from sam.download.
from sam.osm import OSMNetwork
from sam.download.sld import dl_sld
from sam.config import counties
from sam.download.ms_footprints import

# import pytest
TEST_CRS = rputils.create_crs(crs_input=2881)
TEST_STATE = "FL"
TEST_COUNTY = ["12031"]
TEST_COUNTY_NM = "Miami-Dade"
TEST_YEAR = 2019


# Residence area characteristics
def test_dl_rac():
	rac = lodes.rac(state=TEST_STATE, year=TEST_YEAR)
	rac["ctyfips"] = [x[:5] for x in rac.h_geocode]
	rac = rac[rac.ctyfips.isin(TEST_COUNTY)]
	return rac.drop(columns="ctyfips")


def test_rac(df=test_dl_rac()):
	is_df = isinstance(df, pd.DataFrame)
	non_zero = len(df) > 0
	assert is_df + non_zero == 2


# # Workplace area characteristics
def test_dl_wac():
	wac = lodes.wac(state=TEST_STATE, year=TEST_YEAR)
	wac["ctyfips"] = [x[:5] for x in wac.w_geocode]
	wac = wac[wac.ctyfips.isin(TEST_COUNTY)]
	return wac.drop(columns="ctyfips")


def test_wac(df=test_dl_wac()):
	is_df = isinstance(df, pd.DataFrame)
	non_zero = len(df) > 0
	assert is_df + non_zero == 2


# # # Origin-destination jobs
def test_dl_lodes():
	od = lodes.od(state=TEST_STATE, year=TEST_YEAR)
	od["h_ctyfips"] = [x[:5] for x in od.h_geocode]
	od["w_ctyfips"] = [x[:5] for x in od.w_geocode]
	od = od[np.logical_or(od.h_ctyfips.isin(TEST_COUNTY), od.w_ctyfips.isin(TEST_COUNTY))]
	return od.drop(columns=["h_ctyfips", "w_ctyfips"])


def test_od(df=test_dl_lodes()):
	is_df = isinstance(df, pd.DataFrame)
	non_zero = len(df) > 0
	assert is_df + non_zero == 2


# # Geography crosswalk
def test_dl_xwalk():
	return lodes.xwalk(state=TEST_STATE)


def test_od(df=test_dl_xwalk()):
	is_df = isinstance(df, pd.DataFrame)
	non_zero = len(df) > 0
	assert is_df + non_zero == 2


def test_dl_sld():
	aoi = counties.loc[counties.GEOID == TEST_COUNTY[0]]
	return dl_sld(mask=aoi)


def test_sld(df=test_dl_sld()):
	is_df = isinstance(df, pd.DataFrame)
	non_zero = len(df) > 0
	assert is_df + non_zero == 2


# Building Footprints
def test_dl_buildings():
	# Download a dummy AOI
	# aoi = sam.download.census.dl_tiger(geom="counties", state="FL", county="031")
	aoi = sam.download.census.dl_tiger(geom="counties", state=TEST_STATE, county=TEST_COUNTY)
	# Check how much of aoi has "new" building data
	sam.download.ms_footprints.ms_isin_focal_area(aoi)
	# Download buildings within that AOI
	bf = sam.download.ms_footprints.dl_ms_building_footprints(state="", mask=aoi)
# # Jobs files aggregated to block group
# rac_bg = rac.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)
# wac_bg = wac.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)
# od_bg = od.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)

# def test_agg():
#     assert len(rac_bg) == len(
#         xw.loc[xw.tabblk2010.isin(rac.h_geocode.astype(np.int64))].bgrp.unique()
#         )

# Census geographies in Virgina
def test_dl_census_geoms():
# blk = tiger.blocks(state="VA", year=2019, county="51540", crs=2913, trim=True)
# bg = tiger.block_groups(state="VA", year=2019, county="51540", crs=2913, trim=True)
# tct = tiger.tracts(state="VA", year=2019, county=county, crs=2283, trim=True)
# tcts = tiger.tracts(state="VA", year=2019, county=county_names, crs=2913, trim=True)
# co = tiger.counties(state="VA", year=2019, crs=2284, trim=True)
# type(co[co.GEOID.isin(["51003"])])

# test acs variables
# sex = acs.sex(state="VA", year=2019, county=county)
# hh_inc = acs.hh_income(state="VA", year=2019, county=county)
# age = acs.age(state="VA", year=2019, county=county)
# poverty = acs.ratio_of_income_to_poverty_level(
#     state="VA", year=2019, county=county
#     )
# hh_veh = acs.hh_vehicles(state="VA", year=2019, county=county)
# tenure = acs.tenure(state="VA", year=2019, county=county)

# prj_crs = tct.geometry.crs

# walk = OSMNetwork.walk(
#         geometry=tct, add_travel_time=True, crs=prj_crs
#     )
# walk.to_shp(r"C:\Users\U_RPG\Documents\d1")


# bg = tiger.block_groups(state=state, year=year, county=county, crs="ESRI:102658", trim=True)
# blocks = tiger.blocks(state, year, county, crs="ESRI:102658", trim=True)
# blocks.to_file(r"C:\Users\U_RPG\Documents\GitHub\packages\sammie\test_data\RAW\tiger\blocks.shp")
# sex = acs.sex(state=state, year=year, county=county_name

import sam.parcels as spar

df = spar.download_fl_parcels(
	county=TEST_COUNTY_NM,
	crs=TEST_CRS,
	year=2018,
)
print()
