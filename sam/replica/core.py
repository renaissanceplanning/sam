import us
import pandas_gbq 
import pydata_google_auth 

import pandas as pd
import geopandas as gpd
import numpy as np

from sam.config import CRED, replica_regions, is_int
from sam.config.replica_config import age_breaks, age_groups

state = '34'
county = '039'

df = pandas_gbq.read_gbq( 
    f"""
select person_id, BLOCKGROUP as GEOID, age
from `north_atlantic.north_atlantic_2021_Q4_population`
where left(BLOCKGROUP, 5) = '{state}{county}'
    """,
    project_id='replica-customer', 
    credentials=CRED
)

df.age_group = pd.cut(df['age'], bins=age_breaks, labels=age_groups)

df.groupby(["BLOCKGROUP", "age_group"]).agg(
    n = ("person_id", 'size')
).reset_index().pivot(
    index=['BLOCKGROUP'],
    columns='age_group',
    values='n'
).rename_axis(None, axis=1).reset_index()

def find_mega_region(state):
    """_summary_

    Args:
        state (_type_): _description_
    """
    region = "".join(
        {i for i in replica_regions if  "28" in replica_regions[i]}
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
        
    def age(self, age_bins = age_breaks, labels = age_groups):
        pass
