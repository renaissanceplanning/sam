# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 14:30:54 2022

@author: AZ7
"""
import os
os.environ['R_HOME'] = r"C:\ProgramData\Miniconda3\envs\sam\Lib\R"
from sam.lodes import XWalk as xwalk
from sam.lodes import LODES as lodes
from sam.tiger import Tiger as tiger
from sam.acs import ACS as acs

import rputils
import numpy as np

state = "VA"
county = ["51003","51540"]
year = 2019

# Residence area characteristics
rac = lodes.rac(state=state, year=year)
rac["ctyfips"] = [x[:5] for x in rac.h_geocode]
rac = rac[rac.ctyfips.isin(county)]
rac = rac.drop(columns="ctyfips")

# Workplace area characteristics
wac = lodes.wac(state=state, year=year)
wac["ctyfips"] = [x[:5] for x in wac.w_geocode]
wac = wac[wac.ctyfips.isin(county)]
wac = wac.drop(columns="ctyfips")

# Origin-destination jobs
od = lodes.od(state=state, year=year)
od["h_ctyfips"] = [x[:5] for x in od.h_geocode]
od["w_ctyfips"] = [x[:5] for x in od.w_geocode]
od = od[np.logical_or(od.h_ctyfips.isin(county), od.w_ctyfips.isin(county))]
od = od.drop(columns=["h_ctyfips","w_ctyfips"])

# Geography crosswalk
xw = xwalk.xwalk(state=state)

# Jobs files aggregated to block group
rac_bg = rac.aggregate(XWalk=xw, to="bgrp", keepname=False)
wac_bg = rac.aggregate(XWalk=xw, to="bgrp", keepname=False)
od_bg = rac.aggregate(XWalk=xw, to="bgrp", keepname=False)

# Census geographies in Oregon
blk = tiger.blocks(state="VA", year=2019, county=None, crs=2913, trim=True)
bg = tiger.block_groups(state="VA", year=2019, county=None, crs=2913, trim=True)
tct = tiger.tracts(state="VA", year=2019, county=None, crs=2913, trim=True)
co = tiger.counties(state="VA", year=2019, crs=2284, trim=True)
type(co[co.GEOID.isin(["51003"])])



