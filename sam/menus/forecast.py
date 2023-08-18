import os
import us
import datetime
import pandas as pd
import numpy as np
import geopandas as gpd
import osmnx as ox

from sam.parcels import download_fl_parcels
from sam.acs import ACS
from sam.lodes import lodes
from sam.tiger import Tiger as tiger
from sam.lihtc import download_lihtc
from sam.osm import OSMNetwork
from sam.config import PAR_CONF
from sam.config import COUNTIES as county_shapes
from sam.config import extract_fips, validate_data_dir
from sam.config import ACS_CONF
from tqdm import tqdm
from rputils import make_path


def pull_forecast_data(
    summary_areas,
    data_dir,
    prj_crs,
    lodes_data=["rac", "wac", "od"],
    lodes_level="bgrp",
    main_year=None,
    back_years=3,
    pull_parcels=True,
):
    if main_year == None:
        main_year = datetime.date.today().year - 1
        acs_year = main_year - 1
        lodes_year = main_year - 2
    else:
        acs_year = main_year - 1
        lodes_year = main_year - 2

    # validate_data_dir(data_dir)
    data_dir = os.path.normpath(data_dir)
    raw_dir = os.path.join(data_dir, "RAW")
    lodes_dir = os.path.join(raw_dir, "lodes")
    acs_dir = os.path.join(raw_dir, "acs")
    shp_dir = os.path.join(raw_dir, "tiger")
    net_dir = os.path.join(raw_dir, "osm")
    par_dir = os.path.join(raw_dir, "parcels")
    lih_dir = os.path.join(raw_dir, "lihtc")

    for dire in [raw_dir, lodes_dir, acs_dir, shp_dir, net_dir, par_dir, lih_dir]:
        if os.path.exists(dire) != True:
            os.mkdir(dire)

    # pull state fips
    state, counties, county_names = extract_fips(summary_areas)

    # pull parcels (only will work in florida for now)
    # also can only pull main year, other years must be requested

    if pull_parcels:
        print("Downloading parcels...")

        parcels = pd.concat(
            [
                download_fl_parcels(
                    county=county, crs=prj_crs, year=main_year, config=PAR_CONF
                )
                for county in county_names
            ]
        )
        parcels.to_file(os.path.join(par_dir, f"parcels_{main_year}.shp"))
        del parcels

    print("Downloading ACS...")
    for year in tqdm(list(range(acs_year, acs_year - back_years, -1))):
        age = ACS.age_by_sex(state=state, year=year, county=counties)
        age.to_csv(make_path(acs_dir, f"age_by_sex_{year}.csv"))

        total = ACS.totals(state=state, year=year, county=counties)
        total.to_csv(make_path(acs_dir, f"totals_{year}.csv"))

    # download lodes

    print("Downloading LODES...")

    postal = us.states.lookup(state[0]).abbr
    xw = lodes.xwalk(state=postal)

    for year in tqdm(list(range(lodes_year, lodes_year - back_years, -1))):

        if "rac" in lodes_data:
            rac = lodes.rac(state=postal, year=year)
            rac = rac.lodes.aggregate(XWalk=xw, to=lodes_level)
            rac.to_csv(os.path.join(lodes_dir, f"rac_{year}.csv"), index=False)
            del rac

        if "wac" in lodes_data:
            wac = lodes.wac(state=postal, year=year)
            wac = wac.lodes.aggregate(XWalk=xw, to=lodes_level)
            wac.to_csv(os.path.join(lodes_dir, f"wac_{year}.csv"), index=False)
            del wac

        if "od" in lodes_data:
            od = lodes.od(state=postal, year=year)
            # od = od.lodes.aggregate(XWalk=xw, to=lodes_level) TODO fix the aggregate method
            od.to_csv(os.path.join(lodes_dir, f"rac_{year}.csv"), index=False)
            del od

    del xw

    # pull shapes

    print("Downloading TIGER...")

    bgrp = tiger.block_groups(state=state, county=counties)
    bgrp = bgrp.to_crs(prj_crs)
    bgrp.to_file(os.path.join(shp_dir, "block_groups_2010.shp"))
    del bgrp

    bgrp = tiger.block_groups(state=state, county=counties, year=2020)
    bgrp = bgrp.to_crs(prj_crs)
    bgrp.to_file(os.path.join(shp_dir, "block_groups_2020.shp"))
    del bgrp

    blocks = tiger.blocks(state=state, county=counties)
    blocks = blocks.to_crs(prj_crs)
    blocks.to_file(os.path.join(shp_dir, "blocks.shp"))
    del blocks
    
    print("Done! Now go Download BAO")
