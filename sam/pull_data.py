import os
import us
import datetime
import pandas as pd
import numpy as np
import geopandas as gpd
import osmnx as ox 

from sam.parcels import download_fl_parcels  
from sam.acs import acs
from sam.lodes import lodes
from sam.tiger import Tiger as tiger
from sam.osm import OSMNetwork
from sam.config import acs_config, parcel_config

# TODO adjust function to handle states and counties for acs/tiger

# helper functions and variables
expected = np.array(['parcel_year', 'acs_year', 'lodes_year'])

# test values
states, counties = (['12'], ['011'])

def extract_fips(gdf):
    gdf = gdf.geometry.to_crs('wgs 84')
    minx, miny, maxx, maxy = gdf.geometry.total_bounds
    boundaries = ox.geometries_from_bbox(
        maxy, miny, maxx, minx, tags = {'admin_level': "6"}
        )
    counties = boundaries['nist:fips_code'].str[-3:].to_list()
    states = boundaries['nist:fips_code'].str[:-3].unique().tolist() 
    return states, counties

# fetcher
def pull_all_data(summary_areas, 
                  data_dir, 
                  prj_crs,
                  lodes_data = ['rac', 'wac', 'od'],
                  lodes_level = 'bgrp',
                  years = None):
    
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
            raise ValueError(f'{expected[~in_keys]} not in years dict')        
    
    # validate dir
    data_dir = os.path.normpath(data_dir)
    raw_dir = os.path.join(data_dir, "RAW")
    lodes_dir = os.path.join(raw_dir, "lodes")
    acs_dir = os.path.join(raw_dir, "acs")
    shp_dir = os.path.join(raw_dir, "tiger")
    net_dir = os.path.join(raw_dir, "osm")
    par_dir = os.path.join(raw_dir, "parcels")
    
    for dir in [raw_dir, lodes_dir, acs_dir, shp_dir, net_dir, par_dir]:
        if os.path.exists(dir) != True:
            os.mkdir(dir)
        
    # pull state fips    
    # states, counties = extract_fips(summary_areas)
    states, counties = (['12'], ['031'])
    
    # download lodes
    # add handling for differing lodes
    postal = [us.states.lookup(state).abbr
                  for state in states]
    xw = pd.concat([lodes.xwalk(state=pos) for pos in postal])
    
    rac = pd.concat([lodes.rac(state=pos, year=years['lodes_year']) 
                     for pos in postal])
    rac = rac.lodes.aggregate(XWalk=xw, to=lodes_level)
    rac.to_csv(os.path.join(lodes_dir, f"rac_{years['lodes_year']}.csv"))
    
    wac = pd.concat([lodes.wac(state=pos, year=years['lodes_year']) 
                     for pos in postal])
    wac = wac.lodes.aggregate(XWalk=xw, to=lodes_level)
    wac.to_csv(os.path.join(lodes_dir, f"wac_{years['lodes_year']}.csv"))
    
    # od = pd.concat([lodes.od(state=pos, year=years['lodes_year']) 
    #                  for pos in postal])
    # od = od.lodes.aggregate(XWalk=xw, to=lodes_level)
    # od.to_csv(os.path.join(lodes_dir, f"rac_{years['lodes_year']}.csv"))
    
    # del rac, wac, xw, # od
    
    # pull acs TODO make extendable to any new functions without adding code
    sex = pd.concat(
        [acs.sex(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    sex.to_csv(os.path.join(acs_dir, "sex.csv"))
    
    age = pd.concat(
        [acs.age(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    age.to_csv(os.path.join(acs_dir, "age.csv"))
    
    hh_income = pd.concat(
        [acs.hh_income(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    hh_income.to_csv(os.path.join(acs_dir, "hh_income.csv"))
    
    rip = pd.concat(
        [acs.ratio_of_income_to_poverty_level(
            state=state, year=years['acs_year'], county=counties
            )
         for state in states]
        )
    rip.to_csv(os.path.join(acs_dir, "rip.csv"))
    
    hh_vehicles = pd.concat(
        [acs.hh_vehicles(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    hh_vehicles.to_csv(os.path.join(acs_dir, "hh_vehicles.csv"))
    
    tenure = pd.concat(
        [acs.tenure(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    tenure.to_csv(os.path.join(acs_dir, "tenure.csv"))
    
    disability = pd.concat(
        [acs.disability_status(
            state=state, year=years['acs_year'], county=counties
            )
         for state in states]
        )
    disability.to_csv(os.path.join(acs_dir, "disability.csv"))
    
    hh_size = pd.concat(
        [acs.hh_size(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    hh_size.to_csv(os.path.join(acs_dir, "hh_size.csv"))
    
    hh_workers = pd.concat(
        [acs.hh_workers(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    hh_workers.to_csv(os.path.join(acs_dir, "hh_workers.csv"))
    
    education = pd.concat(
        [acs.education(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    education.to_csv(os.path.join(acs_dir, "education.csv"))
    
    race = pd.concat(
        [acs.race(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    race.to_csv(os.path.join(acs_dir, "race.csv"))
    
    ethnicity = pd.concat(
        [acs.ethnicity(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    ethnicity.to_csv(os.path.join(acs_dir, "ethnicity.csv"))
    
    minority_status = pd.concat(
        [acs.minority_status(
            state=state, year=years['acs_year'], county=counties
            )
         for state in states]
        )
    minority_status.to_csv(os.path.join(acs_dir, "minority_status.csv"))
    
    mode_share = pd.concat(
        [acs.mode_share(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    mode_share.to_csv(os.path.join(acs_dir, "mode_share.csv"))
    
    totals = pd.concat(
        [acs.totals(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    totals.to_csv(os.path.join(acs_dir, "totals.csv"))
    
    rent = pd.concat(
        [acs.rent(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    rent.to_csv(os.path.join(acs_dir, "rent.csv"))
    
    value = pd.concat(
        [acs.value(state=state, year=years['acs_year'], county=counties)
         for state in states]
        )
    value.to_csv(os.path.join(acs_dir, "value.csv"))
    
    del (sex, age, hh_income, rip, hh_vehicles, tenure, disability, hh_size,
         hh_workers, education, race, ethnicity, minority_status, 
         mode_share,
         totals, rent, value)
    
    # # pull shapes
    bgrp = gpd.GeoDataFrame(
        pd.concat([tiger.block_groups(state=state, county=counties)
                   for state in states])
    )
    bgrp = bgrp.to_crs(prj_crs)
    bgrp.to_file(os.path.join(shp_dir, "block_groups.shp"))
    del bgrp
    
    # pull parcels (only will work in florida for now)      
    # parcels = pd.concat(
    #     [download_fl_parcels(
    #         county='Broward',
    #         crs=prj_crs,
    #         year=years['parcel_year'],
    #         config=parcel_config.fl_par_config
    #         ) for county in counties]
    # )  
    # parcels.to_file(
    #     os.path.join(par_dir, f'parcels_{years["parcel_year"]}.shp')
    #     )  
    # del parcels
    
    # pull networks
    walk = OSMNetwork.walk(
        geometry=summary_areas, add_travel_time=True, crs=prj_crs
    )
    walk.to_shp(net_dir, "walk")
    del walk
    
    bike = OSMNetwork.bike(
        geometry=summary_areas, add_travel_time=True, crs=prj_crs
    )
    bike.to_shp(net_dir, "bike")
    del bike
    
    drive = OSMNetwork.drive(
        geometry=summary_areas, add_travel_time=True, crs=prj_crs
    )
    drive.to_shp(net_dir, "drive")
    del drive
        
if __name__ == "__main__":
    DATA_DIR = 'C:/Users/U_RPG/Documents/GitHub/packages/sammie/test_data'
               
    summary_area = gpd.read_file(
        os.path.join(DATA_DIR, "RAW/sum_areas/sum_areas.shp")
    )
    
    pull_all_data(summary_areas=summary_area,
                  data_dir=DATA_DIR,
                  prj_crs="ESRI:102658")
