# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 14:30:54 2022

@author: AZ7
"""
#todo clean up tests for automatic testing

import os
import rputils
import numpy as np
import pandas as pd
# os.environ['R_HOME'] = r"C:\Users\U_RPG\anaconda3\envs\sam\lib\R"
from sam.lodes import lodes 
from sam.tiger import Tiger as tiger
from sam.acs import acs
from sam.osm import OSMNetwork

# import pytest
crs = rputils.create_crs(crs_input=2881)
state = "FL"
county = ["12031"]
county_names = "Miami-Dade"
year = 2019

# Residence area characteristics
# rac = lodes.rac(state=state, year=year)
# rac["ctyfips"] = [x[:5] for x in rac.h_geocode]
# rac = rac[rac.ctyfips.isin(county)]
# rac = rac.drop(columns="ctyfips")

# def test_rac(df=rac):
#     is_df = isinstance(df, pd.DataFrame)
#     non_zero = len(df) > 0
#     assert is_df + non_zero == 2 

# # Workplace area characteristics
# wac = lodes.wac(state=state, year=year)
# wac["ctyfips"] = [x[:5] for x in wac.w_geocode]
# wac = wac[wac.ctyfips.isin(county)]
# wac = wac.drop(columns="ctyfips")

# def test_wac(df=wac):
#     is_df = isinstance(df, pd.DataFrame)
#     non_zero = len(df) > 0
#     assert is_df + non_zero == 2 

# # # Origin-destination jobs
# od = lodes.od(state=state, year=year)
# od["h_ctyfips"] = [x[:5] for x in od.h_geocode]
# od["w_ctyfips"] = [x[:5] for x in od.w_geocode]
# od = od[np.logical_or(od.h_ctyfips.isin(county), od.w_ctyfips.isin(county))]
# od = od.drop(columns=["h_ctyfips","w_ctyfips"])

# def test_od(df=od):
#     is_df = isinstance(df, pd.DataFrame)
#     non_zero = len(df) > 0
#     assert is_df + non_zero == 2 


# # Geography crosswalk
# xw = lodes.xwalk(state=state)

# def test_od(df=xw):
#     is_df = isinstance(df, pd.DataFrame)
#     non_zero = len(df) > 0
#     assert is_df + non_zero == 2 

# # Jobs files aggregated to block group
# rac_bg = rac.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)
# wac_bg = wac.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)
# od_bg = od.lodes.aggregate(XWalk=xw, to="bgrp", keepname=False)

# def test_agg():
#     assert len(rac_bg) == len(
#         xw.loc[xw.tabblk2010.isin(rac.h_geocode.astype(np.int64))].bgrp.unique()
#         )

# Census geographies in Virgina
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
df = spar.download_fl_parcels(county=county_names, crs=crs, year=2018,)
print()

