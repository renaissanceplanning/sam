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
from sam.replica import Replica
from sam.nlcd import download_nlcd
from sam.sld import download_sld

from sam.config import PAR_CONF
from sam.config import COUNTIES as county_shapes
from sam.config import extract_fips, validate_data_dir
from sam.config.replica_config import replica_acs_tables
from sam.config.menus import tod_menu

from rputils import make_path

expected = np.array(["parcel_year", "acs_year", "lodes_year"])

class dataMenuDownloader:
    """_summary_
    A class that allows for mass use of the SAM data downloaders.
    
    Contains methods wrapping the individual submodules downloaders so that the (insert pull method name)
    and injest various project menus and settings to provide a convient methods for mass downloads.
    """
    def __init__(
        self,
        summary_areas,
        data_dir,
        prj_crs,
        years=None,
        ):
        self.dirs = validate_data_dir(data_dir=data_dir)
        
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
            
        state, counties, county_names = extract_fips(summary_areas)
        
        self.summary_areas = summary_areas
        self.years = years
        self.postal = us.states.lookup(state[0]).abbr
        self.state = state
        self.counties = counties
        self.county_names = county_names
        self.crs = prj_crs
        self.rep_fetch = Replica(state=state, 
                                 county=counties, 
                                 year=years["parcel_year"])
        
    def pull_lodes(
        self,
        lodes_data=["rac", "wac", "od"],
        lodes_level="bgrp",
        ):
        print("Downloading LODES...")
        
        xw = lodes.xwalk(state=self.postal)

        if "rac" in lodes_data:
            rac = lodes.rac(state=self.postal, year=self.years["lodes_year"])
            rac = rac.lodes.aggregate(XWalk=xw, to=lodes_level)
            rac.to_csv(
                make_path(self.dirs['lodes_dir'], 
                             f"rac_{self.years['lodes_year']}.csv"), 
                index=False
                )

        if "wac" in lodes_data:
            wac = lodes.wac(state=self.postal, year=self.years["lodes_year"])
            wac = wac.lodes.aggregate(XWalk=xw, to=lodes_level)
            wac.to_csv(
                make_path(self.dirs['lodes_dir'], 
                             f"wac_{self.years['lodes_year']}.csv"), 
                index=False
                )

        if "od" in lodes_data:
            od = lodes.od(state=self.postal, year=self.years["lodes_year"])
            # od = od.lodes.aggregate(XWalk=xw, to=lodes_level) TODO fix the aggregate method
            od.to_csv(
                make_path(self.dirs['lodes_dir'], 
                             f"od_{self.years['lodes_year']}.csv"), 
                index=False
                )
            
    def pull_acs(
        self,
    ):
        print("Downloading ACS...")
        # TODO use the get attribute method and a list
        methods = [
            func
            for func in dir(ACS)
            if callable(getattr(ACS, func)) and not func.startswith("__")
        ]

        for method in methods:
            df = getattr(ACS, method)(
                state=self.state, 
                year=self.years["acs_year"], 
                county=self.counties
                )
            if df.empty == False:
                df.to_csv(
                    make_path(
                        self.dirs['acs_dir'], 
                        f"{method}_{self.years['acs_year']}.csv"), 
                    index=False
                    )
            else:
                print(f"{method} returned empty df and is dropped")
                
    def pull_tiger(
        self
    ):
        print("Downloading TIGER...")
        
        bgrp = tiger.block_groups(state=self.state, 
                                  county=self.counties)
        bgrp = bgrp.to_crs(self.crs)
        bgrp.to_file(make_path(self.dirs['shp_dir'], "block_groups_2010.shp"))

        bgrp = tiger.block_groups(state=self.state, 
                                  county=self.counties, 
                                  year=2020)
        bgrp = bgrp.to_crs(self.crs)
        bgrp.to_file(make_path(self.dirs['shp_dir'], "block_groups_2020.shp"))

        blocks = tiger.blocks(state=self.state, 
                              county=self.counties)
        blocks = blocks.to_crs(self.crs)
        blocks.to_file(make_path(self.dirs['shp_dir'], "blocks.shp"))
        
        tracts = tiger.tracts(state=self.state, 
                              county=self.counties)
        tracts = tracts.to_crs(self.crs)
        tracts.to_file(make_path(self.dirs['shp_dir'], "tracts.shp"))
        
    def pull_parcels(
        self,
        parcel_source="replica",
        parcel_replica_fields=True,
    ):
        print("Downloading parcels...")
        if parcel_source == "DOR":
            parcels = pd.concat(
                [
                    download_fl_parcels(
                        county=county,
                        crs=self.crs,
                        year=self.years["parcel_year"],
                        config=PAR_CONF,
                        replica=parcel_replica_fields
                    )
                    for county in self.county_names
                ]
            )
        else:
            rep_fetch = Replica(
                state=self.state, 
                county=self.counties, 
                year=self.years["parcel_year"]
                )
            parcels = rep_fetch.parcels(crs=self.crs)

        parcels.to_file(
            make_path(
                self.dirs['par_dir'], 
                f'parcels_{self.years["parcel_year"]}.shp')
            )
        
    def pull_OSM(
        self,
        add_travel_time=True
    ):
        print("Downloading OSM...")

        walk = OSMNetwork.walk(
            geometry=self.summary_areas, 
            add_travel_time=add_travel_time, 
            crs=self.crs
            )
        walk.to_shp(self.dirs['net_dir'], "walk")

        bike = OSMNetwork.bike(
            geometry=self.summary_areas, 
            add_travel_time=add_travel_time, 
            crs=self.crs
            )
        bike.to_shp(self.dirs['net_dir'], "bike")

        drive = OSMNetwork.drive(
            geometry=self.summary_areas, 
            add_travel_time=add_travel_time, 
            crs=self.crs
            )
        drive.to_shp(self.dirs['net_dir'], "drive")
        
    def pull_lihtc(
            self
        ):
        print("Downloading Low Income Housing...")
        lihtc = download_lihtc(
            state=self.state, 
            county=self.counties, 
            crs=self.crs
            )
        lihtc.to_file(make_path(self.dirs['lih_dir'], "lihtc.shp"))
        
    def pull_nlcd(
            self,
            dataset
        ):
        print("Downloading Replica Trip Table...")
        nlcd = download_nlcd(
            state=self.state,
            counties=self.counties,
            year=self.years["parcel_year"],
            dataset=dataset
        )
        path = dataset.replace(' ', '_')
        
        nlcd = nlcd.reproject(to_crs=self.crs)
        nlcd.to_file(save_path=make_path(self.dirs['nlcd_dir'],
                                            f'{path}.tif'))
            
    def pull_sld(
            self,
            keep_cols
        ):
        print("Downloading Replica SLD...")
        sld = download_sld(
            state=self.state,
            county=self.county,
            keep_cols=keep_cols
        )
        sld.to_file(
            make_path(self.dirs['sld_dir'], "sld.shp")
        )
            
    def pull_replica_trip_table(
            self,
            mid_week=True,
            link_ids=False,
            time="all",  
            purpose="all"
        ):
            print("Downloading Replica Trip Table...")
            org_trips = self.rep_fetch.trip_table(origin=True, 
                                                  link_ids=link_ids, 
                                                  mid_week=mid_week,
                                                  time=time,
                                                  purpose=purpose)
            
            dest_trips = self.rep_fetch.trip_table(origin=False, 
                                                   link_ids=link_ids, 
                                                   mid_week=mid_week,
                                                   time=time,
                                                   purpose=purpose)

            pd.concat([org_trips, dest_trips]).to_csv(
                make_path(self.dirs['rep_dir'], 
                          f"all_trips_{self.rep_fetch._yearSQL}.csv")
            )
            
    def pull_replica_network(
        self
    ):
        print("Downloading Replica Network...")
        network = self.rep_fetch.network(crs=self.crs)
        network.to_file(
            make_path(self.dirs['rep_dir'], 
                      f"network_{self.rep_fetch._yearSQL}.shp")
        )
            
    def pull_replica_acs(
        self,
    ):
        """
        Pull Data From Replica using the ACS Format
        """
        print("Downloading Replica ACS Table...")
        for method in replica_acs_tables:
            df = getattr(self.rep_fetch, method)()
            
            if df.empty == False:
                df.to_csv(make_path(self.dirs['rep_dir'], 
                                    f"{method}_{self.rep_fetch._yearSQL}.csv"), 
                          index=False)
            else:
                print(f"{method} returned empty df and is dropped")
                
    def pull_replica_population(
        self,
    ):
        print("Downloading Replica Population Table...")
        pop = self.rep_fetch.population()
        pop.to_csv(
            make_path(self.dirs['rep_dir'],
                      f"replica_population_{self.rep_fetch._yearSQL}.csv"),
            index=False)
        
    def pull_menu(
        self, methods
    ):
        """Provides a convient way to run many methods at once using their
        default arguments.

        Args:
            methods (dict, optional): Dictonary of methods to run as strings as 
            keys and method arguments as values. The method args values should
            be in their own dict, to use default arguments pass empty dict.
                
        Returns:
            None, saves output to appropriate directory.
        """
        for method, kwargs in methods.items():
            getattr(self, method)(**kwargs)

        
if __name__ == "__main__":
    data_dir = make_path(
        "D:/Renaissance Planning Group",
        "Projects - ComprehensivePlan_2023/tech_group/data"
        )
    
    county = gpd.read_file(make_path(data_dir, 'RAW', "vb_boundary.shp"))
    county.geometry = county.buffer(distance=-1000)
    
    fetcher = dataMenuDownloader(
        county, data_dir, prj_crs=county.crs
    )
    
    fetcher.pull_menu(methods=tod_menu)