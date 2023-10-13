import re
import pandas as pd
import numpy as np
import sam.config.acs_config as acs_cfg
from sam.config.helper_functions import create_geo_dict

from sam.download.sld import dl_sld
geoid = '12115'

def download_sld(geoid, keep_cols=None):
    """downloads and filters sld to study county

    Args:
        state (str): FIPS code
        county (Type, optional): FIPS Code. Defaults to None.
        keep_cols (list, optional): List of SLD columns to keep. Defaults to None.

    Returns:
        gpd.GeoDataFrame: SLD filtered to project location
    """
    if isinstance(geoid, str):
        geoid = [geoid]
    
    sld = dl_sld(columns=keep_cols)
    sld = sld.loc[sld.GEOID20.str[0:5].isin(geoid)]
    return sld

if __name__ == "__main__":
    print(download_sld(geoid=geoid))
