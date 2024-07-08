DC_STATEHOOD = 1
import datetime

import numpy as np
import pandas as pd
import us
from rputils import make_path

from sam.acs import ACS
from sam.config import PAR_CONF
from sam.config import extract_fips, validate_data_dir
from sam.config.helper_functions import create_geo_dict
from sam.config.replica_config import replica_acs_tables
from sam.lihtc import download_lihtc
from sam.lodes import lodes
from sam.nlcd import download_nlcd
from sam.osm import OSMNetwork
from sam.parcels import download_fl_parcels
from sam.replica import Replica
from sam.sld import download_sld
from sam.tiger import Tiger as tiger

expected = np.array(["parcel_year", "acs_year", "lodes_year"])


class dataMenuDownloader:
    """_summary_
    A class that allows for mass use of the SAM data downloaders.
    
    Contains methods wrapping the individual submodules downloaders so that  
    `pull_menu` can injest various project menus and settings to provide a 
    convient methods for mass downloads.
    """

    def __init__(
            self,
            summary_areas,
            data_dir,
            prj_crs,
            years=None,
    ):
        self.dirs = validate_data_dir(data_dir=data_dir)

        if years is None:
            years = {
                "parcel_year": datetime.date.today().year - 1,
                "acs_year": datetime.date.today().year - 2,
                "lodes_year": datetime.date.today().year - 3,
            }
        elif isinstance(years, int):
            years = {
                "parcel_year": years - 1,
                "acs_year": years - 2,
                "lodes_year": years - 3,
            }
        else:
            in_keys = np.array([key in years.keys() for key in expected])
            if sum(in_keys) != 3:
                raise ValueError(f"{expected[~in_keys]} not in years dict")

        geoids, county_names = extract_fips(summary_areas)

        self.summary_areas = summary_areas
        self.years = years
        self.geoids = geoids
        self.geo_dict = create_geo_dict(geoids=geoids)

        us.states.DC

        self.postal = [us.states.lookup(state).abbr
                       if state != "11" else "DC"
                       for state in self.geo_dict.keys()]
        # self.state = self.geo_dict.keys()
        # self.counties = [county[2:5] for county in geoids]
        self.county_names = county_names
        self.crs = prj_crs
        self.rep_fetch = Replica(geoid=self.geoids,
                                 year=years["parcel_year"])

    def pull_lodes(
            self,
            lodes_data=["rac", "wac", "od"],
            lodes_level="bgrp",
    ):
        """
        Downloads LODES (Longitudinal Employer-Household Dynamics) data based on 
        the provided parameters and saves the downloaded data as CSV files in 
        the designated directories.
       
        If "rac" is included in `lodes_data`, it downloads Residence Area 
        Characteristics data and saves it as 'rac_year.csv'.
        
        If "wac" is included in `lodes_data`, it downloads Workplace Area 
        Characteristics data and saves it as 'wac_year.csv'.
       
        If "od" is included in `lodes_data`, it downloads Origin-Destination 
        data and saves it as 'od_year.csv'.

        Args:
            lodes_data (list[str], optional): A list of LODES data types to 
                download. Valid options are "rac" (Residence Area 
                Characteristics), "wac" (Workplace Area Characteristics), and 
                "od" (Origin-Destination). Defaults to ["rac", "wac", "od"].
            lodes_level (str, optional): The geographic level at which the LODES
            data should be aggregated. Valid options include "bgrp" (Block 
            Group), "tract" (Census Tract), and other geographic levels 
            supported by the LODES API. Defaults to "bgrp".

        Note:
            This function requires prior setup of the `postal`, `years`, `dirs`, 
            and other necessary attributes within the class.
        """
        print("Downloading LODES...")

        # rac_out = []
        # wac_out = []
        # od_out = []
        # for postal in self.postal:
        xw = lodes.xwalk(geoid=self.geoids)
        if "rac" in lodes_data:
            rac = lodes.rac(geoid=self.geoids, year=self.years["lodes_year"])
            if lodes_level != "blocks":
                rac = rac.lodes.aggregate(XWalk=xw, to=lodes_level)
            # rac_out.append(rac)

        if "wac" in lodes_data:
            wac = lodes.wac(geoid=self.geoids, year=self.years["lodes_year"])
            if lodes_level != "blocks":
                wac = wac.lodes.aggregate(XWalk=xw, to=lodes_level)
            # wac_out.append(wac)

        if "od" in lodes_data:
            od = lodes.od(geoid=self.geoids, year=self.years["lodes_year"])
            # od = od.lodes.aggregate(XWalk=xw, to=lodes_level) TODO fix the aggregate method
            # od_out.append(od)

        # rac = pd.concat(rac_out)
        # wac = pd.concat(wac_out)
        # od = pd.concat(od_out)

        rac.to_csv(
            make_path(self.dirs['lodes_dir'],
                      f"rac_{self.years['lodes_year']}.csv"),
            index=False
        )

        wac.to_csv(
            make_path(self.dirs['lodes_dir'],
                      f"wac_{self.years['lodes_year']}.csv"),
            index=False
        )

        od.to_csv(
            make_path(self.dirs['lodes_dir'],
                      f"od_{self.years['lodes_year']}.csv"),
            index=False
        )

    def pull_acs(
            self,
    ):
        """
        Downloads American Community Survey (ACS) data for various methods and 
        saves them as CSV files.

        Note:
            This function requires prior setup of the `state`, `years`, 
            `counties`, `dirs`, and other necessary attributes within the class.

        Downloads ACS data using the methods available in the ACS class and 
        saves the downloaded data as CSV files in the designated directories.

        Args:
            None

        Returns:
            None
        """
        print("Downloading ACS...")
        # TODO use the get attribute method and a list
        methods = [
            func
            for func in dir(ACS)
            if callable(getattr(ACS, func)) and not func.startswith("__")
        ]

        for method in methods:
            df = getattr(ACS, method)(
                geoid=self.geoids,
                year=self.years["acs_year"],
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
        """
        Downloads TIGER (Topologically Integrated Geographic Encoding and 
        Referencing) data for specified boundaries.

        This method downloads TIGER data for block groups, blocks, and tracts 
        for the specified state and county, and saves them as shapefiles in the 
        designated directory specified in the `dirs` attribute of the class.
        
        Note:
            This function should be called after setting up the necessary 
            attributes (`state`, `counties`, `crs`, `dirs`) within the class 
            instance.

        Args:
            None

        Returns:
            None
        """
        print("Downloading TIGER...")
        # bgrp_2010_out = []
        # bgrp_2020_out = []
        # blocks_out = []
        # tracts_out = []

        # for geoid in self.geoids:
        bgrp_10 = tiger.block_groups(geoid=self.geoids, year=2019)
        bgrp_10 = bgrp_10.to_crs(self.crs)
        # bgrp_2010_out.append(bgrp_10)

        bgrp_20 = tiger.block_groups(geoid=self.geoids, year=2020)
        bgrp_20 = bgrp_20.to_crs(self.crs)
        # bgrp_2020_out.append(bgrp_20)

        blocks = tiger.blocks(geoid=self.geoids, year=self.years["acs_year"])
        blocks = blocks.to_crs(self.crs)
        # blocks_out.append(blocks)
        if 'GEOID20' in blocks.columns:
            blocks.rename(columns={'GEOID20': 'GEOID'}, inplace=True)
        if 'GEOID10' in blocks.columns:
            blocks.rename(columns={'GEOID10': 'GEOID'}, inplace=True)

        tracts = tiger.tracts(geoid=self.geoids, year=self.years["acs_year"])
        tracts = tracts.to_crs(self.crs)
        # tracts_out.append(tracts)

        # bgrp_10 = gpd.GeoDataFrame(pd.concat(bgrp_2010_out))
        # bgrp_20 = gpd.GeoDataFrame(pd.concat(bgrp_2020_out))
        # blocks = gpd.GeoDataFrame(pd.concat(bgrp_2010_out))
        # tracts = gpd.GeoDataFrame(pd.concat(bgrp_2010_out))

        bgrp_10.to_file(make_path(self.dirs['shp_dir'], "block_groups_2010.shp"))
        bgrp_20.to_file(make_path(self.dirs['shp_dir'], "block_groups_2020.shp"))
        blocks.to_file(make_path(self.dirs['shp_dir'], "blocks.shp"))
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
            # rep_fetch = Replica(
            #     state=self.state, 
            #     county=self.counties, 
            #     year=self.years["parcel_year"]
            #     )
            parcels = self.rep_fetch.parcels(crs=self.crs)

        parcels.to_file(
            make_path(
                self.dirs['par_dir'],
                f'parcels_{self.years["parcel_year"]}.shp')
        )

    def pull_OSM(
            self,
            add_travel_time=True,
            trim=True
    ):
        """
        Downloads parcel data for specified boundaries from either Florida 
        Department of Revenue (FDOR) or Replica and saves it as a shapefile.

        This method downloads parcel data for the specified state and county 
        boundaries from either source. The downloaded parcel data is then saved 
        as a shapefile in the designated directory specified in the `dirs` 
        attribute of the class.

        Note:
            This function should be called after setting up the necessary 
            attributes (`state`, `counties`, `crs`, `years`, `dirs`) within the 
            class instance.

        Args:
            parcel_source (str, optional): The source from which to download 
                parcel data. Valid options are "DOR" (Department of Revenue) or 
                "replica" (Replica source). Defaults to "replica".
            parcel_replica_fields (bool, optional): A boolean indicating whether 
                to include replica-specific fields when downloading parcel data 
                from the Replica source. Defaults to True.

        Returns:
            None
        """
        print("Downloading OSM...")

        walk = OSMNetwork.walk(
            geometry=self.summary_areas,
            add_travel_time=add_travel_time,
            crs=self.crs
        )
        walk.to_shp(self.dirs['net_dir'],
                    prefix=f"walk_{self.years['parcel_year']}",
                    trim=trim)

        bike = OSMNetwork.bike(
            geometry=self.summary_areas,
            add_travel_time=add_travel_time,
            crs=self.crs
        )
        bike.to_shp(self.dirs['net_dir'],
                    prefix=f"bike_{self.years['parcel_year']}",
                    trim=trim)

        drive = OSMNetwork.drive(
            geometry=self.summary_areas,
            add_travel_time=add_travel_time,
            crs=self.crs
        )
        drive.to_shp(self.dirs['net_dir'],
                     prefix=f"drive_{self.years['parcel_year']}",
                     trim=trim)

    def pull_lihtc(
            self
    ):
        """
        Downloads Low-Income Housing Tax Credit (LIHTC) data and saves it as a 
        shapefile.

        This method downloads LIHTC data for the specified state and county 
        boundaries and saves it as a shapefile in the designated directory 
        specified in the `dirs` attribute of the class.

        Note:
            This function should be called after setting up the necessary 
            attributes (`state`, `counties`, `crs`, `dirs`) within the class 
            instance.

        Args:
            None

        Returns:
            None
        """
        print("Downloading Low Income Housing...")
        lihtc = download_lihtc(
            geoid=self.geoids
        )
        lihtc = lihtc.to_crs(self.crs)
        lihtc.to_file(make_path(self.dirs['lih_dir'],
                                f"lihtc_{self.years['parcel_year']}.shp"))

    def pull_nlcd(
            self,
            dataset
    ):
        """
        Downloads National Land Cover Database (NLCD) data and saves it as a 
        GeoTIFF raster.

        This method downloads NLCD data for the specified state and county 
        boundaries and saves it as a GeoTIFF raster in the designated directory 
        specified in the `dirs` attribute of the class. The NLCD dataset can be 
        selected using the `dataset` parameter.

        Note:
            This function should be called after setting up the necessary 
            attributes (`state`, `counties`, `crs`, `dirs`, `years`) within the 
            class instance.

        Args:
            dataset (str): The NLCD dataset to be downloaded.
            NLCD Data Sets:
                - 'land cover change index'
                - 'land cover all years'
                - 'land cover'
                - 'land cover change'
                - 'land cover change pixels'
                - 'developed imperviousness all years'
                - 'developed imperviousness'
                - 'developed imperviousness descriptor'
                - 'developed urban descriptor'
                - 'developed imperviousness change'
                - 'tree canopy cover'
                - 'tree canopy change'

        Returns:
            None
        """
        print("Downloading Replica Trip Table...")
        nlcd = download_nlcd(
            geoid=self.geoids,
            year=self.years["parcel_year"],
            dataset=dataset
        )
        path = dataset.replace(' ', '_')

        nlcd = nlcd.reproject(to_crs=self.crs)
        nlcd.to_file(save_path=make_path(self.dirs['nlcd_dir'],
                                         f'{path}_{self.years["parcel_year"]}.tif')
                     )

    def pull_sld(
            self,
            keep_cols
    ):
        """
        Downloads the Smart Location Database (SLD) data and saves it as a 
        shapefile.

        This method downloads SLD data for the specified state and county 
        boundaries and saves it as a shapefile in the designated directory 
        specified in the `dirs` attribute of the class. The columns to be 
        retained in the downloaded SLD data can be specified using the 
        `keep_cols` parameter.

        Note:
            This function should be called after setting up the necessary 
            attributes (`state`, `county`, `dirs`) within the class instance.

        Args:
            keep_cols (list[str]): A list of column names to be retained in the downloaded SLD data.

        Returns:
            None
        """
        print("Downloading SLD...")
        sld = download_sld(
            geoid=self.geoids,
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

        """
        Downloads Replica Trip Table data for specified parameters and saves it 
        as a CSV file.

        This method downloads Replica Trip Table data for the specified 
        parameters, including trip origin and destination, link IDs, day type, 
        time period, and trip purpose. The downloaded trip table data is then 
        concatenated and saved as a CSV file in the designated directory 
        specified in the `dirs` attribute of the class.

        Note:
            This function should be called after setting up the necessary 
            attributes (`rep_fetch`, `dirs`) within the class instance.

        Args:
            mid_week (bool, optional): A boolean indicating whether to download 
            mid-week trip table data. Defaults to True.
            link_ids (bool, optional): A boolean indicating whether to include 
            link IDs in the downloaded trip table data. Defaults to False.
            time (str, optional): The time period to filter the trip table data, 
                see `Replica.trip_table` for all options
            purpose (str, optional): The trip purpose to filter the trip table.
                see `Replica.trip_table` for all options

        Returns:
            None
        """
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
        """
        Downloads Replica Network data and saves it as a shapefile.

        This method downloads Replica Network data for the specified year and 
        saves it as a shapefile in the designated directory specified in the 
        `dirs` attribute of the class.

        Note:
            This function should be called after setting up the necessary 
            attributes (`rep_fetch`, `dirs`, `crs`) within the class instance.

        Args:
            None

        Returns:
            None
        """
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
        Pulls Data From Replica Population Table and formats it to be comparable
        to the ACS data
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
        """
        Downloads Replica Population Table data and saves it as a CSV file.

        This method downloads Replica Population Table data for the specified 
        year and saves it as a CSV file in the designated directory specified in 
        the `dirs` attribute of the class.

        Note:
            This function should be called after setting up the necessary 
            attributes (`rep_fetch`, `dirs`) within the class instance.

        Args:
            None

        Returns:
            None
        """
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
    pass
    # data_dir = make_path(
    #     "D:/Renaissance Planning Group",
    #     "Projects - ComprehensivePlan_2023/tech_group/data"
    #     )

    # county = gpd.read_file(make_path(data_dir, 'RAW', "vb_boundary.shp"))
    # county.geometry = county.buffer(distance=-1000)

    # fetcher = dataMenuDownloader(
    #     county, data_dir, prj_crs=county.crs
    # )

    # fetcher.pull_menu(methods=tod_menu)
