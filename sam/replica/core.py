import us
import pandas_gbq 
import pydata_google_auth 

import pandas as pd
import geopandas as gpd
import numpy as np

from sam.config import CRED, replica_regions, is_int
from sam.config import replica_config as rpc

state = ['34']
county = ['039', '024']

def find_mega_region(state):
    """_summary_
    Args:
        state (_type_): _description_
    """
    if isinstance(state, list):
        state = state[0] 
        # TODO fix to find multiple states in the same region return error if multi region
    
    region = "".join(
        {i for i in replica_regions if state in replica_regions[i]}
        )
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
    _state : list of str
        The formatted state(s).
    _county : list of str
        The formatted county(s).
    _region : str
        The mega-region that the state(s) belong to.
    _year : int
        The year of interest.
    _stateSQL : str or tuple of str
        The formatted state(s) in a form that can be used in SQL queries.
    _countySQL : str or tuple of str
        The formatted county(s) in a form that can be used in SQL queries.
    """
    
    def __init__(self, state, county, year):
        # format the state
        if isinstance(state, list):
            for st in state:
                if isinstance(st, int):
                    st = str(st).zfill(2)
                if isinstance(st, str):
                    if is_int(st):
                        st = st.zfill(2)
                    else:
                        st = us.states.lookup(st).fips
        else:
            if isinstance(state, int):
                state = [str(state).zfill(2)]
            if isinstance(state, str):
                if is_int(state):
                    state = [state.zfill(2)]
                else:
                    state = [us.states.lookup(state).fips]
                    
        # format counties
        if isinstance(county, list):     
            for ct in county:
                if isinstance(ct, int):
                    ct = str(ct).zfill(3)
                if isinstance(ct, str):
                    if is_int(ct):
                        ct = ct.zfill(3) 
                    else:
                        raise ValueError("County must be in a fips code")  
                
        else:   
            if isinstance(county, int):
                county = [str(county).zfill(3)]
                    
            if isinstance(county, str):
                if is_int(county):
                    county = [county.zfill(3) ]
                else:
                    raise ValueError("County must be in a fips code")
        
        
        self._state = state
        self._county = county
        self._region = find_mega_region(state)
        self._year = year
        
        if len(state) > 1:
            state = tuple(state) 
        else: 
            state = repr(state).replace("[", "(").replace("]", ")")
            
        if len(county) > 1: 
            county = tuple(county) 
        else: 
            county = repr(state).replace("[", "(").replace("]", ")")
            
        self._stateSQL = state
        self._countySQL = county
        
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL}
            """,
            project_id='replica-customer',
            credentials=CRED)

        df = df.groupby(["GEOID", "sex"]).agg(
            n = ("person_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='sex',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).rename(columns={"M":"male", "F":"female"})
        return df
    
    def age(self, bins = rpc.age_breaks, labels = rpc.age_groups):
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL}
            """,
            project_id='replica-customer',
            credentials=CRED)

        df['age_group'] = pd.cut(df['age'], 
                                 bins=bins, 
                                 labels=labels)

        df = df.groupby(["GEOID", "age_group"]).agg(
            n = ("person_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='age_group',
            values='n'
        ).rename_axis(None, axis=1).reset_index()
        return df

    def hh_income(self, 
                  bins = rpc.hh_inc_breaks, 
                  labels = rpc.hh_inc_groups):
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL}
            """,
            project_id='replica-customer',
            credentials=CRED)

        df['hh_inc_group'] = pd.cut(df['household_income'], 
                                    bins=bins, 
                                    labels=labels)

        df = df.groupby(["GEOID", "hh_inc_group"]).agg(
            n = ("household_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='hh_inc_group',
            values='n'
        ).rename_axis(None, axis=1).reset_index()
        return df
    
    def ratio_of_income_to_poverty_level():
        """
        Currently no data in replica
        """
        return print('Currently no data in replica')
    
    def hh_vehicles(self):
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, BLOCKGROUP as GEOID, vehicles
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL}
            """,
            project_id='replica-customer',
            credentials=CRED)

        df = df.groupby(["GEOID", "vehicles"]).agg(
                n = ("household_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='vehicles',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).rename(columns={"zero":"veh_0", 
                          "1":"veh_1", 
                          "2":"veh_2", 
                          "3_plus":"veh_3p", 
                          "GQ":"group_quarter"}
                 )
        return df
    
    def tenure(self):
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, BLOCKGROUP as GEOID, tenure
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL}
            """,
            project_id='replica-customer',
            credentials=CRED)

        df = df.groupby(["GEOID", "tenure"]).agg(
                n = ("household_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='tenure',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).rename(columns={"owener":"own", 
                          "renter":"rent",  
                          "GQ":"group_quarter"}
                 )
        return df
    
    def hh_size(self):
        df = pandas_gbq.read_gbq(
            f"""
            select household_id, person_id, BLOCKGROUP as GEOID, household_size
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL}
            """,
            project_id='replica-customer',
            credentials=CRED)

        df = df.groupby(["GEOID", "household_size"]).agg(
                n = ("household_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='household_size',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).rename(columns={"1_person": "size_1", 
                          "2_person": "size_2",
                          "3_person": "size_3", 
                          "4_person": "size_4",  
                          "5_person": "size_5",
                          "6_person": "size_6", 
                          "7_plus_person": "size_7p"}
                 )
        return df
    
    def hh_worker(self, 
                  bins=rpc.hh_workers_breaks, 
                  labels=rpc.hh_workers_labels):
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL}
            """,
            project_id='replica-customer',
            credentials=CRED)
        
        df.loc[df.employment != 'employed', "employment"] = 'unemployed'

        df = df.groupby(["GEOID", "household_id", "employment"]).agg(
                workers = ("household_id", 'size')
        ).reset_index().pivot(
            index=['GEOID', 'household_id'],
            columns='employment',
            values='workers'
        ).reset_index().fillna(0).drop(columns='unemployed')
        
        df['workers'] = pd.cut(df['employed'], bins=bins, labels=labels)
        
        df = df.groupby(["GEOID", 'workers']).agg(
                n = ("household_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='workers',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index()
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL} AND
                age > 17
            """,
            project_id='replica-customer',
            credentials=CRED)
        
        df = df.groupby(["GEOID", "education"]).agg(
                n = ("person_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='education',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).rename(columns={'k_12': "lths", 
                        #   'under_3': "lths", 
                          'no_school': "lths", 
                          'high_school': "hs", 
                          'some_college': "scndassc",
                          'advanced_degree': "gradprof", 
                          'bachelors_degree': "bach"}
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL} 
            """,
            project_id='replica-customer',
            credentials=CRED)
        
        df = df.groupby(["GEOID", "race"]).agg(
                n = ("person_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='race',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).rename(columns={'american_indian_alaska_native': "aian", 
                          'asian': "asian", 
                          'black_african_american': "black", 
                          'hawaiin_pacific': "nhopi",
                          'other_race_alone': 'other',
                          'two_or_more_races': "twoplus", 
                          'white': "white"}
                 ).fillna(0)
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL} 
            """,
            project_id='replica-customer',
            credentials=CRED)
        
        df = df.groupby(["GEOID", "ethnicity"]).agg(
                n = ("person_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='ethnicity',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).rename(columns={'hispanic_or_latino': "hisp", 
                          'not_hispanic_or_latino': "nonhisp"}
                 ).fillna(0)
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL} 
            """,
            project_id='replica-customer',
            credentials=CRED)
        
        df['minority'] = 'mnty'
        df.loc[(df['ethnicity'] == 'not_hispanic_or_latino') & 
               (df['race'] == 'white'), 'minority'] = 'nonmnty'
        
        df = df.groupby(["GEOID", "minority"]).agg(
                n = ("person_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='minority',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).fillna(0)
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL} 
            """,
            project_id='replica-customer',
            credentials=CRED)
        
        df = df.groupby(["GEOID", "commute_mode"]).agg(
                n = ("person_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='commute_mode',
            values='n'
        ).rename_axis(
            None, axis=1
        ).reset_index(
        ).rename(columns={'biking': "bike", 
                          'carpool': "car_2p", 
                          'driving': "car_1", 
                          'not_working': "not_working", 
                          'transit': "trans", 
                          'walking': "walk", 
                          'worked_from_home': "wfh"}
                 ).fillna(0)
        df['trips'] = (df['bike'] + df['car_2p'] + df['car_1'] + 
                       df['not_working'] + df['trans'] + df['walk'] +
                       df['wfh'])
        
        for col in ['bike', 'car_2p', 'car_1', 
                    'not_working', 'trans', 'walk', 
                    'wfh']:
            df[col] = df[col] / df['trips']
            
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
            from `{self._region}.{self._region}_2021_Q4_population`
            where 
                left(BLOCKGROUP, 2) in {self._stateSQL} AND
                substr(BLOCKGROUP, 3, 3) in {self._countySQL} 
            """,
            project_id='replica-customer',
            credentials=CRED)
        
        pop = df.groupby(["GEOID"]).agg(
                pop = ("person_id", 'size')
        ).reset_index()
        
        hh = (df[['GEOID', 'household_id']]
              .drop_duplicates()
              .groupby(["GEOID"]).agg(
                hh = ("household_id", 'size')
        ).reset_index())
        
        df = pop.merge(hh)
        return df
    
    # def rent():
    #     pass #may not have the data
    
    # def value():
    #     pass #may not have the data
    
    # def cost():
    #     pass #may not have the data
    
nj = Replica(state=state, county=county, year=2020)
nj.mode_share()