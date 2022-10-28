import us
import geopandas as gpd
import numpy as np
import pandas as pd

from io import BytesIO
from urllib import request
from zipfile import ZipFile


def is_int(element):
    try:
        int(element)
        return True
    except ValueError:
        return False

def pull_lihtc(state, county, spatial=True, crs='EPSG:4326'):
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
    
    url = request.urlopen('https://lihtc.huduser.gov/lihtcpub.zip').read()
    files = ZipFile(BytesIO(url))
    lihtc = pd.read_csv(files.open('LIHTCPUB.CSV'))
    
    lihtc = lihtc.loc[
        ~lihtc.st2010.isnull() & ~lihtc.cnty2010.isnull() &
        ~lihtc.st2010.isna() & ~lihtc.cnty2010.isna()
    ].copy()
    
    lihtc.st2010 = lihtc.st2010.astype(str).str.zfill(2)
    lihtc.cnty2010 = lihtc.cnty2010.astype(np.int64).astype(str).str.zfill(3)
    
    lihtc = lihtc.loc[
        lihtc.st2010.isin(state) & lihtc.cnty2010.isin(county)
        ].copy()
    
    if spatial:
        lihtc = gpd.GeoDataFrame(
            lihtc, geometry=gpd.points_from_xy(lihtc.longitude, 
                                               lihtc.latitude,
                                               crs='EPSG:4326')
        )
        if crs != 'EPSG:4326':
            lihtc = lihtc.to_crs(crs=crs)
        
    return lihtc
