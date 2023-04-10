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
    Download Data from Replica's BigQuery 
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
    
    def age(self, age_bins = rpc.age_breaks, labels = rpc.age_groups):
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
                                 bins=rpc.age_breaks, 
                                 labels=rpc.age_groups)

        df = df.groupby(["GEOID", "age_group"]).agg(
            n = ("person_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='age_group',
            values='n'
        ).rename_axis(None, axis=1).reset_index()
        
        return df

    def hh_income(self, 
                  age_bins = rpc.hh_inc_breaks, 
                  labels = rpc.hh_inc_groups):
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
                                    bins=rpc.hh_inc_breaks, 
                                    labels=rpc.hh_inc_groups)

        df = df.groupby(["GEOID", "hh_inc_group"]).agg(
            n = ("household_id", 'size')
        ).reset_index().pivot(
            index=['GEOID'],
            columns='hh_inc_group',
            values='n'
        ).rename_axis(None, axis=1).reset_index()
        
        return df
    
    def hh_vehicles(self, 
                    age_bins = rpc.hh_inc_breaks, 
                    labels = rpc.hh_inc_groups):
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
    
nj = Replica(state=state, county=county, year=2020)