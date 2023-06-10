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
from sam.lihtc import pull_lihtc
from sam.osm import OSMNetwork
from sam.config import PAR_CONF
from sam.config import COUNTIES as county_shapes
from sam.config import extract_fips, validate_data_dir
from sam.replica import Replica
from rputils import make_path

# TODO get postal from county geojson? I think this is done
# TODO add pad and NLCD (NLCD needs default datasets to be incorporated)
# TODO set up downloader to handle differing census geographies by 2030
# TODO add alternatives for Replica data for non-parcel data and add trip downloaders
# TODO replica year automation

# helper functions and variables
expected = np.array(["parcel_year", "acs_year", "lodes_year"])

# fetcher
def pull_corridor_data(
    summary_areas,
    data_dir,
    prj_crs,
    lodes_data=["rac", "wac", "od"],
    lodes_level="bgrp",
    years=None,
    parcel_source="replica",
    network_ids=False,
    trip_table_time="all",
):
    """Download relevant data for a TOD study.

    Args:
        summary_areas (gpd.GeoDataFrame): A gdf containing summary area polygons
        data_dir (str): File path for the data directory
        prj_crs (str): CRS used across the project
        lodes_data (list, optional): Which LODES tables to fetch.
            Defaults to ['rac', 'wac', 'od'].
        lodes_level (str, optional): Which geography to summarize LODES to.
            Defaults to 'bgrp'.
        years (dict, optional): Years for parcel, acs, and lodes data.
            Defaults to current year - 3 for lodes, current year - 2 for ACS,
            and current year -1 for parcels. This should work most of the year,
            but the Florida Parcels can be difficult.
        parcels (bool, optionsl): Download DOR Parcels.

    Raises:
        ValueError: Missing years values in the years dict.
    """
    # fill in appropriate years
    if years == None:
        years = {
            "parcel_year": datetime.date.today().year - 1,
            "acs_year": datetime.date.today().year - 2,
            "lodes_year": datetime.date.today().year - 3,
        }
    else:
        in_keys = np.array([key in years.keys() for key in expected])
        if sum(in_keys) != 3:
            raise ValueError(f"{expected[~in_keys]} not in years dict")

            # validate dir
    data_dir = os.path.normpath(data_dir)
    raw_dir = os.path.join(data_dir, "RAW")
    lodes_dir = os.path.join(raw_dir, "lodes")
    acs_dir = os.path.join(raw_dir, "acs")
    shp_dir = os.path.join(raw_dir, "tiger")
    net_dir = os.path.join(raw_dir, "osm")
    par_dir = os.path.join(raw_dir, "parcels")
    lih_dir = os.path.join(raw_dir, "lihtc")
    rep_dir = os.path.join(raw_dir, "replica")

    for dire in [
        raw_dir,
        lodes_dir,
        acs_dir,
        shp_dir,
        net_dir,
        par_dir,
        lih_dir,
        rep_dir,
    ]:
        if os.path.exists(dire) != True:
            os.mkdir(dire)

    # pull state fips
    state, counties, county_names = extract_fips(summary_areas)

    # download lodes

    print("Downloading LODES...")

    postal = us.states.lookup(state[0]).abbr
    xw = lodes.xwalk(state=postal)

    if "rac" in lodes_data:
        rac = lodes.rac(state=postal, year=years["lodes_year"])
        rac = rac.lodes.aggregate(XWalk=xw, to=lodes_level)
        rac.to_csv(
            os.path.join(lodes_dir, f"rac_{years['lodes_year']}.csv"), index=False
        )
        del rac

    if "wac" in lodes_data:
        wac = lodes.wac(state=postal, year=years["lodes_year"])
        wac = wac.lodes.aggregate(XWalk=xw, to=lodes_level)
        wac.to_csv(
            os.path.join(lodes_dir, f"wac_{years['lodes_year']}.csv"), index=False
        )
        del wac

    if "od" in lodes_data:
        od = lodes.od(state=postal, year=years["lodes_year"])
        # od = od.lodes.aggregate(XWalk=xw, to=lodes_level) TODO fix the aggregate method
        od.to_csv(os.path.join(lodes_dir, f"od_{years['lodes_year']}.csv"), index=False)
        del od

    del xw

    # pull acs TODO make extendable to any new functions without adding code

    print("Downloading ACS...")

    # TODO use the get attribute method and a list

    methods = [
        func
        for func in dir(ACS)
        if callable(getattr(ACS, func)) and not func.startswith("__")
    ]

    for method in methods:
        df = getattr(ACS, method)(state=state, year=years["acs_year"], county=counties)
        if df.empty == False:
            df.to_csv(os.path.join(acs_dir, f"{method}.csv"), index=False)
        else:
            print(f"{method} returned empty df and is dropped")

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

    if parcel_source != None:
        print("Downloading parcels...")
        if parcel_source == "DOR":
            parcels = pd.concat(
                [
                    download_fl_parcels(
                        county=county,
                        crs=prj_crs,
                        year=years["parcel_year"],
                        config=PAR_CONF,
                    )
                    for county in county_names
                ]
            )
        else:
            rep_fetch = Replica(state=state, county=counties, year=years["parcel_year"])
            parcels = rep_fetch.parcels(crs=prj_crs)

        parcels.to_file(os.path.join(par_dir, f'parcels_{years["parcel_year"]}.shp'))
        del parcels

    # pull networks

    print("Downloading OSM...")

    walk = OSMNetwork.walk(geometry=summary_areas, add_travel_time=True, crs=prj_crs)
    walk.to_shp(net_dir, "walk")
    del walk

    bike = OSMNetwork.bike(geometry=summary_areas, add_travel_time=True, crs=prj_crs)
    bike.to_shp(net_dir, "bike")
    del bike

    drive = OSMNetwork.drive(geometry=summary_areas, add_travel_time=True, crs=prj_crs)
    drive.to_shp(net_dir, "drive")
    del drive

    print("Downloading Low Income Housing...")
    lihtc = pull_lihtc(state=state, county=counties, crs=prj_crs)
    lihtc.to_file(os.path.join(lih_dir, "lihtc.shp"))

    print("Set Up Replica Fetcher")
    rep_fetch = Replica(state=state, county=counties, year=years["parcel_year"])

    print("Downloading Replica Trip Table...")
    org_trips = rep_fetch.trip_table(link_ids=network_ids, time=trip_table_time)
    # org_trips.to_csv(
    #     make_path(rep_dir, f"origin_trips_{years['parcel_year']}.csv")
    #     )

    dest_trips = rep_fetch.trip_table(link_ids=network_ids, time=trip_table_time)
    # dest_trips.to_csv(
    #     make_path(rep_dir, f"dest_trips_{years['parcel_year']}.csv")
    #     )

    pd.concat([org_trips, dest_trips]).to_file(
        make_path(rep_dir, f"all_trips_{years['parcel_year']}.csv")
    )

    print("Downloading Replica Network...")
    network = rep_fetch.network(crs=prj_crs)
    network.to_file(make_path(rep_dir, "network.shp"))


if __name__ == "__main__":
    pass
