import us
import geopandas as gpd
import numpy as np
import pandas as pd
import urllib3

from io import BytesIO
from urllib.request import Request, urlopen
from zipfile import ZipFile
from sam.config import is_int
from sam.config.ref_config import COUNTIES


def download_lihtc(geoid):
    """Pull LIHTC from HUD

    Args:
        geometry (GeoDataFrame): GDF of area to pull values.

    

    Returns:
        gpd.GeoDataFrame: LIHTC point level dataframe
    """
    if isinstance(geoid, list):
        for id in geoid:
            if isinstance(id, int):
                st = str(id).zfill(5)
            if isinstance(id, str):
                if is_int(id):
                    id = id.zfill(5)
                else:
                    st = us.states.lookup(st).fips #probably drop
    else:
        if isinstance(geoid, int):
            geoid = [str(geoid).zfill(5)]
        if isinstance(geoid, str):
            if is_int(geoid):
                geoid = [state.zfill(5)]
            else:
                state = [us.states.lookup(state).fips] #probably drop

    # if isinstance(county, list):
    #     for ct in county:
    #         if isinstance(ct, int):
    #             ct = str(ct).zfill(3)
    #         if isinstance(ct, str):
    #             if is_int(ct):
    #                 ct = ct.zfill(3)
    #             else:
    #                 raise ValueError("County must be in a fips code")
    # else:
    #     if isinstance(county, int):
    #         county = [str(county).zfill(3)]

    #     if isinstance(county, str):
    #         if is_int(county):
    #             county = [county.zfill(3)]
    #         else:
    #             raise ValueError("County must be in a fips code")
    
    std_ctys = COUNTIES.loc[COUNTIES['GEOID'].isin(geoid)]

    # url = request.urlopen('https://lihtc.huduser.gov/lihtcpub.zip').read()
    req = Request(
        url='https://lihtc.huduser.gov/lihtcpub.zip', 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    url = urlopen(req).read()
    
    files = ZipFile(BytesIO(url))
    lihtc = pd.read_csv(files.open("LIHTCPUB.CSV"))
    lihtc = gpd.GeoDataFrame(
            lihtc,
            geometry=gpd.points_from_xy(
                lihtc.longitude, lihtc.latitude, crs="EPSG:4326"
            ),
        )
    
    lihtc = lihtc.to_crs(std_ctys.crs)
    keep_cols = lihtc.columns
    
    lihtc = lihtc.sjoin(std_ctys, op='within')
    lihtc = lihtc[keep_cols].copy()

    # lihtc = lihtc.loc[
    #     ~lihtc.st2010.isnull()
    #     & ~lihtc.cnty2010.isnull()
    #     & ~lihtc.st2010.isna()
    #     & ~lihtc.cnty2010.isna()
    #     & ~(lihtc.cnty2010 == ".")
    # ].copy()

    # lihtc.st2010 = lihtc.st2010.astype(str).str.zfill(2)
    # lihtc.cnty2010 = lihtc.cnty2010.astype(np.int64).astype(str).str.zfill(3)

    # lihtc = lihtc.loc[lihtc.st2010.isin(state) & lihtc.cnty2010.isin(county)].copy()

    return lihtc
