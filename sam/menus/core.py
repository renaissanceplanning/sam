"""
Data menu downloader for SAM library.

This module provides the DataMenuDownloader class for batch downloading
various geographic and demographic data sources.
"""
DC_STATEHOOD = 1
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import geopandas as gpd
import numpy as np
import pandas as pd
import us
# from rputils import make_path  # Not used - only in commented examples

logger = logging.getLogger(__name__)

from sam.acs import ACS
from sam.config import PAR_CONF
from sam.config import extract_fips, validate_data_dir
from sam.config.helper_functions import create_geo_dict, ensure_dir_exists
from sam.config.replica_config import replica_acs_tables
from sam.lihtc import download_lihtc
from sam.lodes import lodes
# OSM import is optional - requires algi/rputils dependencies
try:
    from sam.osm import OSMNetwork
    HAS_OSM = True
except ImportError as e:
    logger.warning(f"OSM import failed: {e}")
    OSMNetwork = None
    HAS_OSM = False
except Exception as e:
    logger.warning(f"Unexpected error importing OSM: {e}")
    OSMNetwork = None
    HAS_OSM = False
from sam.parcels import download_fl_parcels
from sam.replica import Replica
from sam.sld import download_sld
from sam.tiger import Tiger as tiger
from sam.download.nlcd import download_nlcd

EXPECTED_YEAR_KEYS = ["parcel_year", "acs_year", "lodes_year"]


class DataMenuDownloader:
    """
    A class for batch downloading SAM data from multiple sources.
    
    This class wraps individual data downloader modules to provide a convenient
    interface for downloading multiple datasets with consistent configuration.
    
    Attributes:
        dirs: Dictionary of data directory paths
        years: Dictionary of years for different data sources
        geoids: List of geographic identifiers (FIPS codes)
        geo_dict: Dictionary mapping state codes to county codes
        postal: List of state postal abbreviations
        county_names: List of county names
        summary_areas: GeoDataFrame of summary areas
        crs: Coordinate reference system
        rep_fetch: Replica data fetcher instance
    """

    def __init__(
        self,
        summary_areas: gpd.GeoDataFrame,
        data_dir: Union[str, Path],
        prj_crs: Optional[str] = None,
        years: Optional[Union[int, Dict[str, int]]] = None,
    ):
        """
        Initialize the DataMenuDownloader.

        Args:
            summary_areas: GeoDataFrame containing area of interest polygons.
            data_dir: Root directory for data storage.
            prj_crs: Project coordinate reference system. If None, uses summary_areas CRS.
            years: Year specification for data downloads. Can be:
                - None: Uses default years (current year - offset)
                - int: Base year, offsets applied automatically
                - dict: Explicit years for each data source with keys:
                    'parcel_year', 'acs_year', 'lodes_year'

        Raises:
            ValueError: If years dict is missing required keys.
        """
        # Initialize directory structure (but don't create directories yet)
        self.dirs = validate_data_dir(data_dir=data_dir)
        
        # Process years configuration
        self.years = self._process_years(years)
        
        # Extract geographic information
        geoids, county_names = extract_fips(summary_areas)
        self.geoids = geoids
        self.geo_dict = create_geo_dict(geoids=geoids)
        self.county_names = county_names
        
        # Get state postal codes
        self.postal = [
            us.states.lookup(state).abbr if state != "11" else "DC"
            for state in self.geo_dict.keys()
        ]
        
        # Store other attributes
        self.summary_areas = summary_areas
        # Use provided CRS or fallback to summary_areas CRS
        self.crs = prj_crs if prj_crs is not None else summary_areas.crs
        
        # Initialize Replica fetcher
        self.rep_fetch = Replica(
            geoid=self.geoids,
            year=self.years["parcel_year"]
        )
        
        logger.info(
            f"Initialized DataMenuDownloader for {len(self.geoids)} counties: "
            f"{', '.join(self.county_names)}"
        )

    @staticmethod
    def _process_years(years: Optional[Union[int, Dict[str, int]]]) -> Dict[str, int]:
        """
        Process years input into standardized dictionary.

        Args:
            years: Year specification (None, int, or dict).

        Returns:
            Dictionary with keys 'parcel_year', 'acs_year', 'lodes_year'.

        Raises:
            ValueError: If dict is missing required keys.
        """
        current_year = datetime.date.today().year
        
        if years is None:
            return {
                "parcel_year": current_year - 1,
                "acs_year": current_year - 2,
                "lodes_year": current_year - 3,
            }
        
        if isinstance(years, int):
            return {
                "parcel_year": years - 1,
                "acs_year": years - 2,
                "lodes_year": years - 3,
            }
        
        # Validate dictionary input
        missing_keys = [key for key in EXPECTED_YEAR_KEYS if key not in years]
        if missing_keys:
            raise ValueError(
                f"Years dictionary missing required keys: {missing_keys}. "
                f"Required: {EXPECTED_YEAR_KEYS}"
            )
        
        return years

    def pull_lodes(self, lodes_data: List[str] = None, lodes_level: str = "bgrp",) -> None:
        """
        Download LODES (Longitudinal Employer-Household Dynamics) data.

        Downloads employment data from the U.S. Census Bureau's LODES program
        and saves as CSV files.
       
        If "rac" is included in `lodes_data`, it downloads Residence Area 
        Characteristics data and saves it as 'rac_year.csv'.
        
        If "wac" is included in `lodes_data`, it downloads Workplace Area 
        Characteristics data and saves it as 'wac_year.csv'.
       
        If "od" is included in `lodes_data`, it downloads Origin-Destination 
        data and saves it as 'od_year.csv'.

        Args:
            lodes_data: List of LODES datasets to download. Options:
                - 'rac': Residence Area Characteristics
                - 'wac': Workplace Area Characteristics
                - 'od': Origin-Destination flow data
                Default: ['rac', 'wac', 'od']
            lodes_level: Geographic aggregation level. Options:
                - 'bgrp': Block Group (default)
                - 'blocks': Census Block
                - Other levels supported by LODES API

        Returns:
            None. Saves CSV files to the lodes directory.
        """
        if lodes_data is None:
            lodes_data = ["rac", "wac", "od"]
        
        # Create lodes directory only when needed
        lodes_dir = ensure_dir_exists(self.dirs['lodes_dir'])

        logger.info("Downloading LODES data...")

        # Get crosswalk for aggregation
        xw = lodes.xwalk(geoid=self.geoids)

        # Download RAC (Residence Area Characteristics)
        if "rac" in lodes_data:
            logger.info("Downloading LODES RAC (Residence Area Characteristics)...")
            rac = lodes.rac(geoid=self.geoids, year=self.years["lodes_year"])

            if lodes_level != "blocks":
                rac = rac.lodes.aggregate(XWalk=xw, to=lodes_level)
            out_f = lodes_dir / f"rac_{self.years['lodes_year']}.csv"
            rac.to_csv(out_f, index=False)
            logger.info(f"Saved RAC data to {out_f}")

        # Download WAC (Workplace Area Characteristics)
        if "wac" in lodes_data:
            logger.info("Downloading LODES WAC (Workplace Area Characteristics)...")
            wac = lodes.wac(geoid=self.geoids, year=self.years["lodes_year"])

            if lodes_level != "blocks":
                wac = wac.lodes.aggregate(XWalk=xw, to=lodes_level)

            out_f = lodes_dir / f"wac_{self.years['lodes_year']}.csv"
            wac.to_csv(out_f, index=False)
            logger.info(f"Saved WAC data to {out_f}")

        # Download OD (Origin-Destination)
        if "od" in lodes_data:
            logger.info("Downloading LODES OD (Origin-Destination)...")
            od = lodes.od(geoid=self.geoids, year=self.years["lodes_year"])

            # TODO: fix the aggregate method for OD data
            # if lodes_level != "blocks":
            #     od = od.lodes.aggregate(XWalk=xw, to=lodes_level)

            out_f = lodes_dir / f"od_{self.years['lodes_year']}.csv"
            od.to_csv(out_f, index=False)
            logger.info(f"Saved OD data to {out_f}")

    def pull_acs(self) -> None:
        """
        Download American Community Survey (ACS) data.

        Downloads all available ACS tables and saves them as CSV files.
        Uses reflection to find all ACS methods dynamically.

        Returns:
            None. Saves CSV files to the acs directory.
        """
        # Create ACS directory only when needed
        acs_dir = ensure_dir_exists(self.dirs['acs_dir'])

        logger.info(f"Downloading ACS data for year {self.years['acs_year']}")

        # Get all ACS methods dynamically
        methods = [
            func
            for func in dir(ACS)
            if callable(getattr(ACS, func)) and not func.startswith("__")
        ]

        logger.info(f"Found {len(methods)} ACS methods to process")

        for method in methods:

            try:
                df = getattr(ACS, method)(
                    geoid=self.geoids,
                    year=self.years["acs_year"],
                )

                if not df.empty:
                    output_file = acs_dir / f"{method}_{self.years['acs_year']}.csv"
                    df.to_csv(output_file, index=False)
                    logger.info(f"Saved {method} to {output_file}")
                else:
                    logger.warning(f"ACS {method} returned empty DataFrame, skipping")

            except Exception as e:
                logger.error(f"Failed to process ACS {method}: {e}")

    def pull_tiger(self) -> None:
        """
        Download TIGER/Line geographic boundary files.

        Downloads Census TIGER/Line shapefiles for block groups (2010 and 2020),
        blocks, and tracts for the specified counties.

        Returns:
            None. Saves shapefiles to the tiger directory.
        """
        # Create tiger directory only when needed
        shp_dir = ensure_dir_exists(self.dirs['shp_dir'])

        logger.info("Downloading TIGER/Line shapefiles")

        # Download 2010 Block Groups
        try:
            logger.info("Downloading TIGER block groups (2010)...")
            bgrp_10 = tiger.block_groups(geoid=self.geoids, year=2019)
            bgrp_10 = bgrp_10.to_crs(self.crs)
            bgrp_10.to_file(shp_dir / "block_groups_2010.shp")
            logger.info(f"Saved 2010 block groups to {shp_dir / 'block_groups_2010.shp'}")
        except Exception as e:
            logger.error(f"Failed to download 2010 block groups: {e}")

        # Download 2020 Block Groups
        try:
            logger.info("Downloading TIGER block groups (2020)...")
            bgrp_20 = tiger.block_groups(geoid=self.geoids, year=2020)
            bgrp_20 = bgrp_20.to_crs(self.crs)
            bgrp_20.to_file(shp_dir / "block_groups_2020.shp")
            logger.info(f"Saved 2020 block groups to {shp_dir / 'block_groups_2020.shp'}")
        except Exception as e:
            logger.error(f"Failed to download 2020 block groups: {e}")

        # Download Blocks (always use decennial year for proper block definitions)
        try:
            logger.info("Downloading TIGER blocks (2020 decennial)...")
            blocks = tiger.blocks(geoid=self.geoids, year=2020)
            blocks = blocks.to_crs(self.crs)

            # Handle different GEOID column names across years
            if 'GEOID20' in blocks.columns:
                blocks.rename(columns={'GEOID20': 'GEOID'}, inplace=True)
            if 'GEOID10' in blocks.columns:
                blocks.rename(columns={'GEOID10': 'GEOID'}, inplace=True)

            blocks.to_file(shp_dir / "blocks.shp")
            logger.info(f"Saved blocks to {shp_dir / 'blocks.shp'}")
        except Exception as e:
            logger.error(f"Failed to download blocks: {e}")

        # Download Tracts
        try:
            logger.info("Downloading TIGER tracts...")
            tracts = tiger.tracts(geoid=self.geoids, year=self.years["acs_year"])
            tracts = tracts.to_crs(self.crs)
            tracts.to_file(shp_dir / "tracts.shp")
            logger.info(f"Saved tracts to {shp_dir / 'tracts.shp'}")
        except Exception as e:
            logger.error(f"Failed to download tracts: {e}")

    def pull_parcels(self, parcel_source: str = "replica", parcel_replica_fields: bool = True, keep_raw: bool = False) -> None:
        """
        Download parcel data from either Florida DOR or Replica.

        Downloads parcel data for the specified counties from either the Florida
        Department of Revenue (FDOR) or Replica and saves as a shapefile.

        Args:
            parcel_source: Source for parcel data. Options:
                - 'DOR': Florida Department of Revenue (FDOR official data)
                - 'replica': Replica parcel data (default)
            parcel_replica_fields: Whether to format fields for Replica compatibility.
                If True, applies Replica-specific field mappings and transformations.
                Default: True

        Returns:
            None. Saves parcel shapefile to the parcels directory.
            
        Notes:
            - DOR source is only available for Florida counties
            - Replica source works for any county in Replica coverage area
            - When parcel_source='DOR' and parcel_replica_fields=True, DOR data
              is formatted to match Replica field schema
        """
        # Create parcels directory only when needed
        par_dir = ensure_dir_exists(self.dirs['par_dir'])

        logger.info("Downloading parcels...")

        if parcel_source == "DOR":
                # Download from Florida Department of Revenue
                logger.info("Downloading parcels from Florida DOR...")
                print(f"  Downloading parcels for {len(self.county_names)} counties from Florida DOR...")

                # Download each county separately
                parcel_list = []
                county_data = []  # Track (county_name, parcels, year) tuples

                for i, county in enumerate(self.county_names, 1):
                    logger.info(f"  Downloading {county} County parcels...")
                    print(f"  [{i}/{len(self.county_names)}] {county} County...")

                    # Download parcels with optional raw data
                    result = download_fl_parcels(
                        county=county,
                        crs=self.crs,
                        year=self.years["parcel_year"],
                        config=PAR_CONF,
                        replica=parcel_replica_fields,
                        keep_raw=keep_raw
                    )

                    # Unpack based on keep_raw setting
                    if keep_raw:
                        county_parcels, raw_gis, county_year = result
                        # Save raw file if requested
                        raw_output = par_dir / f"parcels_{county}_{county_year}_raw.shp"
                        print(f"      Saving raw GIS data: {raw_output.name}")
                        raw_gis.to_file(raw_output, driver='ESRI Shapefile')
                        print(f"      ✓ Saved {len(raw_gis):,} raw parcels (geometry only)")
                    else:
                        county_parcels = result
                        # Get actual data year from this county's parcels
                        if 'DATA_YEAR' in county_parcels.columns:
                            county_year = int(county_parcels['DATA_YEAR'].mode()[0])
                        else:
                            county_year = self.years["parcel_year"]

                    county_data.append((county, county_parcels, county_year))
                    parcel_list.append(county_parcels)
                    print(f"      ✓ Downloaded {len(county_parcels):,} parcels from {county} ({county_year} data)")

                # Determine if we should save separately or combined
                if len(self.county_names) == 1:
                    # Single county - save just that one
                    county, parcels, actual_year = county_data[0]
                    print(f"  Data vintage: {actual_year}")
                else:
                    # Multiple counties - save each separately
                    print(f"  Saving {len(self.county_names)} counties individually...")
                    for county, county_parcels, county_year in county_data:
                        county_output = par_dir / f"parcels_{county}_{county_year}.shp"
                        print(f"    Saving {county} County: {county_output.name}")
                        county_parcels.to_file(county_output, driver='ESRI Shapefile')
                        logger.info(f"Saved {county} County parcels to {county_output}")
                        print(f"      ✓ Saved {len(county_parcels):,} parcels")

                    # Also save a combined file for convenience
                    print(f"  Creating combined file with all {len(self.county_names)} counties...")
                    parcels = pd.concat(parcel_list, ignore_index=True)
                    actual_year = int(parcels['DATA_YEAR'].mode()[0]) if 'DATA_YEAR' in parcels.columns else self.years["parcel_year"]

                    print(f"  ✓ Combined total: {len(parcels):,} parcels")
                    print(f"  Data vintage: {actual_year}")

        else:  # parcel_source == "replica"
            # Download from Replica
            logger.info("Downloading parcels from Replica...")
            parcels = self.rep_fetch.parcels(crs=self.crs)
            actual_year = self.years["parcel_year"]

        # Save to Shapefile format
        if parcel_source == "DOR" and len(self.county_names) == 1:
            # Single county - use county name in filename
            output_file = par_dir / f"parcels_{self.county_names[0]}_{actual_year}.shp"
        else:
            # Multiple counties or Replica - use generic name
            output_file = par_dir / f"parcels_{actual_year}.shp"

        print(f"  Saving to: {output_file}")
        parcels.to_file(output_file, driver='ESRI Shapefile')
        logger.info(f"Saved parcels to {output_file}")
        print(f"  ✓ Saved {len(parcels):,} parcels to {output_file.name}")

    def pull_lihtc(self) -> None:
        """
        Download Low Income Housing Tax Credit (LIHTC) data.

        Downloads LIHTC property data and saves as shapefile.

        Returns:
            None. Saves LIHTC data to the lihtc directory.
        """
        # Create LIHTC directory only when needed
        lih_dir = ensure_dir_exists(self.dirs['lih_dir'])

        logger.info("Downloading LIHTC data")

        try:
            lihtc = download_lihtc()

            output_file = lih_dir / "lihtc.shp"
            lihtc.to_file(output_file)
            logger.info(f"Saved LIHTC data to {output_file}")

        except Exception as e:
            logger.error(f"Failed to download LIHTC: {e}")

    def pull_OSM(self, add_travel_time=True, trim=True ) -> None:
        """
        Download OpenStreetMap (OSM) network data.

        Downloads street network data from OpenStreetMap and saves as shapefile.

        Returns:
            None. Saves network shapefile to the osm directory.
        """
        logger.debug(f"pull_OSM called - HAS_OSM={HAS_OSM}, OSMNetwork={OSMNetwork}")
        if not HAS_OSM:
            logger.error(f"OSM functionality not available - HAS_OSM={HAS_OSM}")
            logger.error(f"OSMNetwork value: {OSMNetwork}")
            logger.error("Missing dependencies: algi, gary, rputils, or osmnx")
            logger.error("Install with: pip install -e C:/github/packages/algi")
            logger.error("Install with: pip install -e C:/github/packages/gary")
            logger.error("Install with: pip install -e C:/github/packages/rputils")
            logger.error("Install with: pip install osmnx")
            raise ImportError("OSM functionality requires algi, gary, rputils, and osmnx packages")

        # Create OSM directory only when needed
        net_dir = ensure_dir_exists(self.dirs['net_dir'])
        logger.info("Downloading OSM network data")

        network_types = ['walk', 'bike', 'drive']
        try:
            for net_type in network_types:
                logger.info(f"Downloading {net_type} network...")
                net_meth = getattr(OSMNetwork, net_type)

                network = net_meth(geometry=self.summary_areas,
                                   add_travel_time=add_travel_time,
                                   crs=self.crs
                )
                prefix = f"{net_type}_network_{self.years['parcel_year']}"
                network.to_shp(save_dir=net_dir, prefix=prefix, trim=trim)
                logger.info(f"Saved {net_type} network to {net_dir}")

        except Exception as e:
            logger.error(f"Failed to download OSM network: {e}")

    def pull_nlcd(self, dataset: Union[str, list[str], None] = None, clip_to_aoi: bool = True) -> None:
        """
        Download National Land Cover Database (NLCD) data.

        Downloads NLCD raster data for the project area. The method automatically
        selects the closest available NLCD year to the project's parcel year.

        **Updated Feb 2026:** Now supports Annual NLCD products (2019-2024) with new
        MRLC URLs. Old S3 bucket URLs no longer work.

        Args:
            dataset: Type(s) of NLCD data to download. Can be a string, list, or None:
                - None: Download all available datasets (land_cover + impervious + tree_canopy) - DEFAULT
                - 'land_cover': Land cover classification only ✓
                - 'impervious': Fractional impervious surface only (0-100%) ✓
                - 'tree_canopy': Tree canopy cover (annual 1985-2023, USFS) ✓
                - 'impervious_descriptor': Not yet available ✗
                - ['land_cover', 'impervious']: Download specific multiple datasets
            clip_to_aoi: If True, automatically clips the raster to the project's
                summary areas after download. If False, downloads full regional
                tile. Default: True (matches original behavior)

        Returns:
            None. Downloads NLCD file(s) to the nlcd directory.

        Notes:
            - Land Cover & Impervious: Annual NLCD 2019-2024 (MRLC)
            - Tree Canopy: Annual 1985-2023 (USDA Forest Service v2023-5)
            - Tree Canopy files are larger (~3.6 GB vs ~1.3 GB for other products)
            - Legacy NLCD years: 2021, 2019, 2016, 2013, 2011, 2008, 2006, 2004, 2001
            - With clip_to_aoi=True: Requires rasterio, creates clipped GeoTIFF, deletes zips
            - With clip_to_aoi=False: Downloads full tile as zip file, keeps zips

        Examples:
            >>> # Download all available datasets (land_cover + impervious + tree_canopy)
            >>> fetcher.pull_nlcd()

            >>> # Download only land cover
            >>> fetcher.pull_nlcd('land_cover')

            >>> # Download only tree canopy
            >>> fetcher.pull_nlcd('tree_canopy')

            >>> # Download specific multiple datasets
            >>> fetcher.pull_nlcd(['land_cover', 'impervious'])

            >>> # Download without clipping (full tile)
            >>> fetcher.pull_nlcd(clip_to_aoi=False)
        """
        # Import here to avoid circular imports
        from sam.download.nlcd import download_nlcd, get_closest_nlcd_year
        from sam.config.helper_functions import ensure_dir_exists

        # Create NLCD directory only when needed
        nlcd_dir = ensure_dir_exists(self.dirs['nlcd_dir'])

        # Get the target year and find closest NLCD year
        target_year = self.years['parcel_year']
        nlcd_year = get_closest_nlcd_year(target_year)

        # Default to all available datasets if none specified
        if dataset is None:
            datasets = ['land_cover', 'impervious', 'tree_canopy']  # All available NLCD products
            logger.info(f"No dataset specified, downloading all available products")
        elif isinstance(dataset, str):
            datasets = [dataset]
        else:
            datasets = dataset

        logger.info(f"Downloading NLCD data...")
        logger.info(f"  Datasets: {', '.join(datasets)}")
        if nlcd_year != target_year:
            logger.info(f"  Note: Requested year {target_year}, using closest available year {nlcd_year}")
        else:
            logger.info(f"  Year: {nlcd_year}")

        # Download each dataset
        downloaded_files = []
        for ds in datasets:
            try:
                logger.info(f"  Downloading {ds}...")

                # Set output path
                if clip_to_aoi:
                    output_filename = f"nlcd_{nlcd_year}_{ds}_clipped.tif"
                else:
                    output_filename = f"nlcd_{nlcd_year}_{ds}.zip"

                output_path = nlcd_dir / output_filename

                # Download NLCD data (with optional clipping)
                downloaded_path = download_nlcd(
                    geoid=self.geoids,
                    year=target_year,
                    dataset=ds,
                    output_path=nlcd_dir / f"nlcd_{nlcd_year}_{ds}.zip",
                    clip_to_aoi=clip_to_aoi,
                    summary_areas=self.summary_areas
                )

                downloaded_files.append(downloaded_path)
                logger.info(f"    ✓ Saved to: {downloaded_path}")

            except Exception as e:
                logger.error(f"    ✗ Failed to download {ds}: {e}")
                logger.info("    Troubleshooting:")
                logger.info("    - Check your internet connection")
                logger.info("    - Verify NLCD data is available at https://www.mrlc.gov/data")
                logger.info("    - If clip_to_aoi=True, ensure rasterio is installed: pip install rasterio")
                logger.info("    - Some datasets may not be available for all years")

        # Summary
        if downloaded_files:
            logger.info(f"\n✓ Downloaded {len(downloaded_files)}/{len(datasets)} NLCD datasets")
            if not clip_to_aoi:
                logger.info("Next steps:")
                logger.info("1. Extract the zip files")
                logger.info("2. Clip the rasters to your area of interest if needed")
        else:
            logger.error("Failed to download any NLCD datasets")

    def pull_sld(self, keep_cols: Optional[List[str]] = None) -> None:
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
        # Create SLD directory only when needed
        sld_dir = ensure_dir_exists(self.dirs['sld_dir'])

        logger.info("Downloading School District boundaries")

        try:
            sld = download_sld(geoid=self.geoids, keep_cols=keep_cols)

            output_file = sld_dir / "sld.shp"
            sld.to_file(output_file)
            logger.info(f"Saved SLD data to {output_file}")

        except Exception as e:
            logger.error(f"Failed to download SLD: {e}")
        
    def pull_replica_trip_table(
        self,
        mid_week: bool = True,
        link_ids: bool = False,
        time: str = "all",
        purpose: str = "all",
        vehicle_type: str = "all"
    ) -> None:

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
        # Create replica directory only when needed
        rep_dir = ensure_dir_exists(self.dirs['rep_dir'])

        logger.info(
            f"Downloading Replica Trip Table "
            f"(mid_week={mid_week}, time={time}, purpose={purpose})"
        )
        try:
            org_trips = self.rep_fetch.trip_table(origin=True, link_ids=link_ids,
                                                mid_week=mid_week, time=time,
                                                purpose=purpose, vehicle_type=vehicle_type)

            dest_trips = self.rep_fetch.trip_table(origin=False, link_ids=link_ids,
                                                mid_week=mid_week, time=time,
                                                purpose=purpose, vehicle_type=vehicle_type)

            # build outfile based on download selections
            purposes = '_'.join([purpose] if isinstance(purpose, str) else purpose)
            filename = f"{time}_{purposes}_trips_{self.rep_fetch._yearSQL}.csv"
            output_file = rep_dir / filename
            pd.concat([org_trips, dest_trips]).to_csv(output_file, index=False)
            logger.info(f"Saved trip table to {output_file}")

        except Exception as e:
            logger.error(f"Failed to download Replica trip table: {e}")

    def pull_replica_network(self) -> None:
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
        # Create replica directory only when needed
        rep_dir = ensure_dir_exists(self.dirs['rep_dir'])

        logger.info("Downloading Replica Network")

        try:
            network = self.rep_fetch.network(crs=self.crs)

            output_file = rep_dir / f"network_{self.rep_fetch._yearSQL}.shp"
            network.to_file(output_file)
            logger.info(f"Saved Replica network to {output_file}")

        except Exception as e:
            logger.error(f"Failed to download Replica network: {e}")
        

    def pull_replica_acs(self) -> None:
        """
        Pulls Data From Replica Population Table and formats it to be comparable
        to the ACS data
        """
        # Create replica directory only when needed
        rep_dir = ensure_dir_exists(self.dirs['rep_dir'])
        logger.info("Downloading Replica ACS tables")
        for method in replica_acs_tables:
            try:
                df = getattr(self.rep_fetch, method)()

                if not df.empty:
                    output_file = rep_dir / f"{method}_{self.rep_fetch._yearSQL}.csv"
                    df.to_csv(output_file, index=False)
                    logger.info(f"Saved {method} to {output_file}")
                else:
                    logger.warning(f"Replica {method} returned empty DataFrame, skipping")

            except Exception as e:
                logger.error(f"Failed to process Replica {method}: {e}")


    def pull_replica_population(self) -> None:
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
        # Create replica directory only when needed
        rep_dir = ensure_dir_exists(self.dirs['rep_dir'])
        logger.info("Downloading Replica Population Table")
        try:
            pop = self.rep_fetch.population()

            output_file = rep_dir / f"replica_population_{self.rep_fetch._yearSQL}.csv"
            pop.to_csv(output_file, index=False)
            logger.info(f"Saved population data to {output_file}")

        except Exception as e:
            logger.error(f"Failed to download Replica population: {e}")
        

    def pull_menu(self, methods: Dict[str, Dict]) -> None:
        """
        Provides a convient way to run many methods at once using their
        default arguments.

        Args:
            methods (dict, optional): Dictonary of methods to run as strings as 
            keys and method arguments as values. The method args values should
            be in their own dict, to use default arguments pass empty dict.
        
        Example:
            >>> fetcher = DataMenuDownloader(aoi, data_dir)
            >>> menu = {
            ...     'pull_acs': {},
            ...     'pull_lodes': {'lodes_data': ['rac', 'wac']},
            ...     'pull_tiger': {}
            ... }
            >>> fetcher.pull_menu(menu)   

        Returns:
            None, saves output to the appropriate directory.
        """
        logger.info(f"Executing pull_menu with {len(methods)} methods")

        for method_name, kwargs in methods.items():
            logger.info(f"Executing method: {method_name}")

            try:
                method = getattr(self, method_name)
                method(**kwargs)
            except AttributeError:
                logger.error(f"Method '{method_name}' not found on DataMenuDownloader")
            except Exception as e:
                logger.error(f"Error executing {method_name}: {e}")
        

if __name__ == "__main__":
    pass
    # from sam.config import COUNTIES
    # from sam.config import replic_persons_trips
    # data_dir = make_path(
    #     "D:/Renaissance Planning Group",
    #     "Projects - ComprehensivePlan_2023/tech_group/data"
    #     )

    # county = gpd.read_file(make_path(data_dir, 'RAW', "vb_boundary.shp"))
    # county.geometry = county.buffer(distance=-1000)

    # fetcher = DataMenuDownloader(
    #     county, data_dir, prj_crs=county.crs
    # )

    # fetcher.pull_menu(methods=replic_persons_trips)
