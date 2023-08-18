import re
import pandas as pd
import numpy as np
import sam.config.acs_config as acs_cfg

from sam.download.sld import dl_sld


def download_sld(state, county=None, keep_cols=None):
    """downloads and filters sld to study county

    Args:
        state (str): FIPS code
        county (Type, optional): FIPS Code. Defaults to None.
        keep_cols (list, optional): List of SLD columns to keep. Defaults to None.

    Returns:
        gpd.GeoDataFrame: SLD filtered to project location
    """
    sld = dl_sld(columns=keep_cols)
    if county is None:
        sld = sld.loc[(sld.STATEFP == state)]
    else:
        sld = sld.loc[(sld.STATEFP == state) & (sld.COUNTYFP == county)]
    return sld
