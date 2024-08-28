import us
import pandas_gbq
import warnings

import pandas as pd
import geopandas as gpd

from sam.config import replica_regions, is_int, replica_config as rpc
from sam.config.parcel_config import rep_parcel_shorten
from shapely import wkt
from sam.config import COUNTIES
from sam.config import CRED
from sam.config.helper_functions import create_geo_dict


# TODO add rputils iterable
# TODO add properties, getter and setter


class YearOutOfBounds(UserWarning):
    pass


def find_mega_region(state):
    """
    Return the mega region where the given state is located.

    Args:
        state (str or list): The state name or list of state names to search for.
            If a list is provided, only the first element is used.

    Returns:
        str: The mega region code where the state is located, as a string.

    Raises:
        ValueError: If the given state or its mega region is not found in the list of known
            mega regions.
    """
    if isinstance(state, list):
        state = state[0]
        # TODO fix to find multiple states in the same region return error if multi region

    region = "".join({i for i in replica_regions if state in replica_regions[i]})
    return region


class Replica:
    """
    A class for downloading data from Replica's BigQuery.

    Parameters
    ----------
    state : str, int, or list of str or int
        The state(s) of interest. If a string or integer is passed,
        it will be converted to a list. If a list is passed, the items
        will be checked and formatted accordingly.
    county : str, int, or list of str or int
        The county(s) of interest. If a string or integer is passed,
        it will be converted to a list. If a list is passed, the items
        will be checked and formatted accordingly.
    year : int
        The year of interest.

    Attributes
    ----------
    _geoid : list of str
        The formatted county(s).
    _region : str
        The mega-region that the state(s) belong to.
    _year : int
        The year of interest.
    _geoidSQL : str or tuple of str
        The formatted geoid(s) in a form that can be used in SQL queries.
    """

    def __init__(self, geoid, year):
        # format the GEOID
        if isinstance(geoid, list):
            for id in geoid:
                if isinstance(id, int):
                    st = str(id).zfill(5)
                if isinstance(id, str):
                    if is_int(id):
                        id = id.zfill(5)
                    else:
                        id = us.states.lookup(
                            st
                        ).fips  # probably replace but likely this formatting is unessesary
        else:
            if isinstance(geoid, int):
                geoid = [str(geoid).zfill(5)]
            if isinstance(geoid, str):
                if is_int(geoid):
                    geoid = [geoid.zfill(5)]
                else:
                    geoid = [
                        us.states.lookup(geoid).fips
                    ]  # probably replace but likely this formatting is unessesary

        # # format counties
        # if isinstance(county, list):
        #     for ct in county:
        #         if isinstance(ct, int):
        #             ct = str(ct).zfill(3)
        #         if isinstance(ct, str):
        #             if is_int(ct):
        #                 ct = ct.zfill(3)
        #             else:
        #                 raise ValueError("County must be a fips code")

        # else:
        #     if isinstance(county, int):
        #         county = [str(county).zfill(3)]

        #     if isinstance(county, str):
        #         if is_int(county):
        #             county = [county.zfill(3)]
        #         else:
        #             raise ValueError("County must be a fips code")

        geo_dict = create_geo_dict(geoids=geoid)

        self._state = geo_dict.keys()
        self._geoid = geoid
        # self._county = county
        self._region = find_mega_region(list(geo_dict.keys()))
        self._year = year

        # format state and counties for SQL
        if len(geoid) > 1:
            geoid = tuple(geoid)
        else:
            geoid = repr(geoid).replace("[", "(").replace("]", ")")

        # if len(county) > 1:
        #     county = tuple(county)
        # else:
        #     county = repr(county).replace("[", "(").replace("]", ")")

        self._geoidSQL = geoid
        # self._countySQL = county

        # Format year for SQL
        if isinstance(year, int):
            if year in rpc.replica_coverage_years:
                if f"{year}_Q4" in rpc.replica_pop_years:
                    self._yearSQL = f"{year}_Q4"
                else:
                    self._yearSQL = f"{year}_Q2"
            else:
                warnings.warn(
                    f"year must be after 2019, excluding 2020 current year is {year}"
                )
        elif isinstance(year, str):
            if year in rpc.replica_pop_years:
                self._yearSQL = year
            else:
                raise ValueError(f"year must be one of {rpc.replica_pop_years}")
        else:
            raise ValueError(f"year must be a str or int, currnetly {type(year)}")

    def sex(self):
        """
        Query Replica's Google BigQuery database for sex information for a
        given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing columns for `person_id`,
        `GEOID` (which is equal to `BLOCKGROUP`), and `sex`.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select person_id, BLOCKGROUP as GEOID, sex
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL}
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df = (
            df.groupby(["GEOID", "sex"])
            .agg(n=("person_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="sex", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .rename(columns={"M": "male", "F": "female"})
        )
        return df

    def age(self, bins=rpc.age_breaks, labels=rpc.age_groups):
        """
        Query the Google BigQuery database for age information for a
        given region, state, and county.

        Args:
        bins (list): A list of bin edges for creating age groups.
            Defaults to `rpc.age_breaks`.
        labels (list): A list of labels for the age groups.
            Defaults to `rpc.age_groups`.

        Returns:
        df (pandas.DataFrame): DataFrame containing counts of individuals in
                            each age group and GEOID combination. Columns are
                            age groups, index is GEOIDs.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select person_id, BLOCKGROUP as GEOID, age
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL}
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels)

        df = (
            df.groupby(["GEOID", "age_group"])
            .agg(n=("person_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="age_group", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
        )
        return df

    def hh_income(self, bins=rpc.hh_inc_breaks, labels=rpc.hh_inc_groups):
        """
        Query the Google BigQuery database for household income information for
        a given region, state, and county.

        Args:
        bins (list): A list of bin edges for creating age groups.
            Defaults to `rpc.age_breaks`.
        labels (list): A list of labels for the age groups.
            Defaults to `rpc.age_groups`.

        Returns:
        df (pandas.DataFrame): DataFrame containing counts of households in
            each income group and GEOID combination.
            Columns are income groups, index is GEOIDs.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, BLOCKGROUP as GEOID, household_income
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL}
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df["hh_inc_group"] = pd.cut(df["household_income"], bins=bins, labels=labels)

        df = (
            df.groupby(["GEOID", "hh_inc_group"])
            .agg(n=("household_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="hh_inc_group", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
        )
        return df

    # def ratio_of_income_to_poverty_level():
    #     """
    #     Currently no data in replica
    #     """
    #     return print('Currently no data in replica')

    def hh_vehicles(self):
        """
        Query the Google BigQuery database for household vehicle information for
        a given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing counts of households in
            each vehicle group and GEOID combination.
            Columns are income groups, index is GEOIDs.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, BLOCKGROUP as GEOID, vehicles
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL}
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df = (
            df.groupby(["GEOID", "vehicles"])
            .agg(n=("household_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="vehicles", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .rename(
                columns={
                    "zero": "veh_0",
                    "1": "veh_1",
                    "2": "veh_2",
                    "3_plus": "veh_3p",
                    "GQ": "group_quarter",
                }
            )
        )
        return df

    def tenure(self):
        """
        Query the Google BigQuery database for household tenure information for
        a given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing counts of households by
        tenure status and GEOID combination.
            Columns are income groups, index is GEOIDs.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, BLOCKGROUP as GEOID, tenure
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL}
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df = (
            df.groupby(["GEOID", "tenure"])
            .agg(n=("household_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="tenure", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .rename(columns={"owener": "own", "renter": "rent", "GQ": "group_quarter"})
        )
        return df

    def hh_size(self):
        """
        Query the Google BigQuery database for household size information for
        a given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing counts of households by
        size and GEOID combination.
            Columns are income groups, index is GEOIDs.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, person_id, BLOCKGROUP as GEOID, household_size
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL}
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df = (
            df.groupby(["GEOID", "household_size"])
            .agg(n=("household_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="household_size", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .rename(
                columns={
                    "1_person": "size_1",
                    "2_person": "size_2",
                    "3_person": "size_3",
                    "4_person": "size_4",
                    "5_person": "size_5",
                    "6_person": "size_6",
                    "7_plus_person": "size_7p",
                }
            )
        )
        return df

    def hh_worker(self, bins=rpc.hh_workers_breaks, labels=rpc.hh_workers_labels):
        """
        Query the Google BigQuery database for household worker information for
        a given region, state, and county.

        Args:
        bins (list): A list of bin edges for creating age groups.
            Defaults to `rpc.hh_workers_breaks`.
        labels (list): A list of labels for the age groups.
            Defaults to `rpc.hh_workers_labels`.

        Returns:
        df (pandas.DataFrame): DataFrame containing counts of households in
            each worker group and GEOID combination.
            Columns are worker groups, index is GEOIDs.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, BLOCKGROUP as GEOID, employment
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL}
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df.loc[df.employment != "employed", "employment"] = "unemployed"

        df = (
            df.groupby(["GEOID", "household_id", "employment"])
            .agg(workers=("household_id", "size"))
            .reset_index()
            .pivot(
                index=["GEOID", "household_id"], columns="employment", values="workers"
            )
            .reset_index()
            .fillna(0)
            .drop(columns="unemployed")
        )

        df["workers"] = pd.cut(df["employed"], bins=bins, labels=labels)

        df = (
            df.groupby(["GEOID", "workers"])
            .agg(n=("household_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="workers", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
        )
        return df

    def education(self):
        """
        Query Replica Google BigQuery database for educational attainment for a
        given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing columns for `GEOID`, counts
            of educational attainment.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select person_id, BLOCKGROUP as GEOID, education
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL} AND
                age > 17
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df = (
            df.groupby(["GEOID", "education"])
            .agg(n=("person_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="education", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .rename(
                columns={
                    "k_12": "lths",
                    #   'under_3': "lths",
                    "no_school": "lths",
                    "high_school": "hs",
                    "some_college": "scndassc",
                    "advanced_degree": "gradprof",
                    "bachelors_degree": "bach",
                }
            )
        )
        return df

    def race(self):
        """
        Query Replica Google BigQuery database for race for a
        given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing columns for `GEOID`, counts
            of each race.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, person_id, BLOCKGROUP as GEOID, race
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL} 
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df = (
            df.groupby(["GEOID", "race"])
            .agg(n=("person_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="race", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .rename(
                columns={
                    "american_indian_alaska_native": "aian",
                    "asian": "asian",
                    "black_african_american": "black",
                    "hawaiin_pacific": "nhopi",
                    "other_race_alone": "other",
                    "two_or_more_races": "twoplus",
                    "white": "white",
                }
            )
            .fillna(0)
        )
        return df

    def ethnicity(self):
        """
        Query Replica Google BigQuery database for ethnicity for a
        given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing columns for `GEOID`, counts
        of hispanic and non hispanic residents.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, person_id, BLOCKGROUP as GEOID, ethnicity
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL} 
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df = (
            df.groupby(["GEOID", "ethnicity"])
            .agg(n=("person_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="ethnicity", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .rename(
                columns={
                    "hispanic_or_latino": "hisp",
                    "not_hispanic_or_latino": "nonhisp",
                }
            )
            .fillna(0)
        )
        return df

    def minority_status(self):
        """
        Query Replica Google BigQuery database for minority status for a
        given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing columns for `GEOID`, counts
        of minority and non minority residents.
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, person_id, BLOCKGROUP as GEOID, ethnicity, race
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL} 
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df["minority"] = "mnty"
        df.loc[
            (df["ethnicity"] == "not_hispanic_or_latino") & (df["race"] == "white"),
            "minority",
        ] = "nonmnty"

        df = (
            df.groupby(["GEOID", "minority"])
            .agg(n=("person_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="minority", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .fillna(0)
        )
        return df

    def mode_share(self):
        """
        Query Replica Google BigQuery database for mode share for a
        given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing columns for `GEOID`, mode
            share and trip totals
        """
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, person_id, BLOCKGROUP as GEOID, commute_mode
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL} 
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df = (
            df.groupby(["GEOID", "commute_mode"])
            .agg(n=("person_id", "size"))
            .reset_index()
            .pivot(index=["GEOID"], columns="commute_mode", values="n")
            .rename_axis(None, axis=1)
            .reset_index()
            .rename(
                columns={
                    "biking": "bike",
                    "carpool": "car_2p",
                    "driving": "car_1",
                    "not_working": "not_working",
                    "transit": "trans",
                    "walking": "walk",
                    "worked_from_home": "wfh",
                }
            )
            .fillna(0)
        )
        df["trips"] = (
            df["bike"]
            + df["car_2p"]
            + df["car_1"]
            + df["not_working"]
            + df["trans"]
            + df["walk"]
            + df["wfh"]
        )

        for col in ["bike", "car_2p", "car_1", "not_working", "trans", "walk", "wfh"]:
            df[col] = df[col] / df["trips"]

        return df

    def totals(self):
        """
        Query the Google BigQuery database for pop and household totals for a
        given region, state, and county.

        Returns:
        df (pandas.DataFrame): DataFrame containing columns for `GEOID` and
            counts of population and households.
        """
        # missing Housing Units
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, person_id, BLOCKGROUP as GEOID
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL} 
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        pop = df.groupby(["GEOID"]).agg(pop=("person_id", "size")).reset_index()

        hh = (
            df[["GEOID", "household_id"]]
            .drop_duplicates()
            .groupby(["GEOID"])
            .agg(hh=("household_id", "size"))
            .reset_index()
        )

        df = pop.merge(hh)
        return df

    # def rent():
    #     pass #may not have the data

    # def value():
    #     pass #may not have the data

    # def cost():
    #     pass #may not have the data

    def trip_table(
        self,
        origin=True,
        mid_week=True,
        link_ids=False,
        time="am",  # TODO add start and end hours
        purpose="all",
        vehicle_type="all"
    ):
        """
        Returns a Pandas DataFrame containing Replica trip data for the
        specified geographic region, filtered by various parameters.

        Args:
            origin (bool): If True, filters trips with the region of interest
                as the origin. If False, filters trips with the region of
                interest as the destination. Defaults to True.
            mid_week (bool): If True, pulls from the midweek table. If False,
                pulls from the weekend table. Defaults to True.
            link_ids (bool): If True, includes link IDs in the output DataFrame.
                If False, does not include link IDs. Defaults to False. Adding
                link ids increases the processing load from 50 gb to 400gb
            time (str): One of "am", "pm", "md", or "all". If "am",
                filters trips that occurred between 6am and 10am.
                If "pm", filters trips that occurred between 4pm and 7pm. If
                "md", filters trips that occurred between 11am and 1pm. If
                "all", does not filter based on time of day. Defaults to "am".
            purpose (str or list): One or more of "COMMERCIAL", "EAT", "HOME",
                "LODGING", "MAINTENANCE", or "OTHER". If a string, filters trips
                with the specified purpose. If a list, filters trips with any of
                the specified purposes. If "all", does not filter based on
                purpose. Defaults to "all".

        Returns:
            pandas.DataFrame: A DataFrame containing the following columns:
        """
        day = "saturday"
        end = "destination"

        if mid_week:
            day = "thursday"

        if origin:
            end = "origin"

        columns = """
        activity_id, person_id, household_id, mode, travel_purpose, tour_type,
        previous_activity_type, timezone, start_time, end_time, start_local_hour,
        end_local_hour, duration_minutes, distance_miles, vehicle_type,
        vehicle_fuel_type, vehicle_fuel_technology, origin_bgrp, origin_bgrp_lat,
        origin_bgrp_lng, destination_bgrp, destination_bgrp_lat, 
        destination_bgrp_lng, origin_land_use_l1, origin_land_use_l2,
        origin_building_use_l1, origin_building_use_l2, destination_land_use_l1, 
        destination_land_use_l2, destination_building_use_l1, 
        destination_building_use_l2
        """

        if link_ids:
            columns = """
            activity_id, person_id, household_id, mode, travel_purpose, tour_type,
            previous_activity_type, timezone, start_time, end_time, start_local_hour,
            end_local_hour, duration_minutes, distance_miles, vehicle_type,
            vehicle_fuel_type, vehicle_fuel_technology, origin_bgrp, origin_bgrp_lat,
            origin_bgrp_lng, destination_bgrp, destination_bgrp_lat, 
            destination_bgrp_lng, origin_land_use_l1, origin_land_use_l2,
            origin_building_use_l1, origin_building_use_l2, destination_land_use_l1, 
            destination_land_use_l2, destination_building_use_l1, 
            destination_building_use_l2, network_link_ids, transit_route_ids
            """

        if time == "am":
            time_filter = "start_local_hour >= 6 and start_local_hour <= 10"
        elif time == "pm":
            time_filter = "start_local_hour >= 16 and start_local_hour <= 19"
        elif time == "md":
            time_filter = "start_local_hour >= 11 and start_local_hour <= 13"
        elif time == "all":
            time_filter = "start_local_hour >= 0 and start_local_hour <= 23"
        else:
            raise ValueError("time must be one of am, pm, md, or all")

        if isinstance(purpose, list):
            for value in purpose:
                if value not in rpc.valid_purposes:
                    raise ValueError(f"values not in {rpc.valid_purposes}")
            purpose_sql = repr(purpose).replace("[", "(").replace("]", ")")
            purpose_filter = f"travel_purpose in {purpose_sql}"
        elif purpose == "all":
            purpose_filter = f"travel_purpose in {rpc.valid_purposes}".replace(
                "[", "("
            ).replace("]", ")")
        elif purpose in rpc.valid_purposes:
            purpose_filter = f"travel_purpose = '{purpose}'"
        else:
            raise ValueError(f"values not in {rpc.valid_purposes}")
        
        if isinstance(vehicle_type, list):
            for value in vehicle_type:
                if value not in rpc.valid_vehicle:
                    raise ValueError(f"values not in {rpc.valid_vehicle}")
            vehicle_sql = repr(vehicle_type).replace("[", "(").replace("]", ")")
            vehicle_filter = f"vehicle_type in {vehicle_sql}"
        elif vehicle_type == "all":
            vehicle_filter = f"travel_purpose in {rpc.valid_vehicle}".replace(
                "[", "("
            ).replace("]", ")")
        elif vehicle_type in rpc.valid_vehicle:
            vehicle_filter = f"travel_purpose = '{purpose}'"
        else:
            raise ValueError(f"values not in {rpc.valid_vehicle}")

        df = pandas_gbq.read_gbq(
            f"""
            select 
                {columns}
            from `{self._region}.{self._region}_{self._yearSQL}_{day}_trip`
            where 
                left({end}_bgrp, 5) in {self._geoidSQL} AND
                {time_filter} AND
                {purpose_filter} AND
                {vehicle_filter}
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df["trip_start"] = "inside"

        if origin != True:
            df["trip_start"] = "outside"

        return df

    # def employment(self):
    #     """_summary_ #TODO fill out to RAC standard"""
    #     pass

    def parcels(self, crs="WGS84"):
        """
        Query Replica Google BigQuery database for parcel table

        Args:
            crs (string): String specifying a CRS for the parcels. Defaults to
                WGS84
        Returns:
            gdf (gpd.GeoDataFrame): GeoDataFrame of the parcel table

        """
        if self._yearSQL not in rpc.replica_parcel_years:
            raise ValueError(
                f"Parcels only available for {rpc.replica_parcel_years}",
                f"not {self._yearSQL}",
            )
        df = pandas_gbq.read_gbq(
            f"""
            select *
            from `{self._region}_landuse.{self._region}_{self._yearSQL}_landuse_parcels`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL} 
                """,
            project_id="replica-customer",
            credentials=CRED,
        )
        df["geometry"] = df.geometry.apply(wkt.loads)  # TODO look at pure geopandas
        gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="WGS84")
        # geometry checking to ensure all geometry is of the same type
        gdf = gdf.loc[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].copy()

        if crs != "WGS84":
            gdf = gdf.to_crs(crs=crs)
        gdf = gdf.rename(columns=rep_parcel_shorten)
        return gdf

    def network(self, crs="WGS84"):
        """
        Query Replica Google BigQuery database for network table

        Args:
            crs (string): Sring specifiying a CRS for the network. Defaults to
                WGS84
        Returns:
            gdf (gpd.GeoDataFrame): GeoDataFrame of the Network table

        """
        df = pandas_gbq.read_gbq(
            f"""
            select *
            from `{self._region}.{self._region}_{self._yearSQL}_network_segments`
            """,
            project_id="replica-customer",
            credentials=CRED,
        )

        df["geometry"] = df.geometry.apply(wkt.loads)  # TODO look at pure geopandas
        gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="WGS84")

        cnty = COUNTIES.loc[COUNTIES.GEOID.isin(self._geoid)].to_crs(crs="WGS84")

        network = gdf.sjoin(cnty[["GEOID", "geometry"]])
        if crs != "WGS84":
            network = network.to_crs(crs=crs)

        return network

    def population(self):
        """
        Query Replica Google BigQuery database for population table

        Returns:
        df (pandas.DataFrame): DataFrame of the population table
        """
        df = pandas_gbq.read_gbq(
            f"""
            select *
            from `{self._region}.{self._region}_{self._yearSQL}_population`
            where 
                left(BLOCKGROUP, 5) in {self._geoidSQL} 
            """,
            project_id="replica-customer",
            credentials=CRED,
        )
        return df


if __name__ == "__main__":
    pass
    # from pprint import pprint
    # state = ['34']
    # county = ['039', '024']
    # nj = Replica(state=state, county=county, year=2023)
    # test = nj.population()
    # pprint(test)
