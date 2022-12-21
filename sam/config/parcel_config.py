import pandas as pd
import numpy as np

fl_par_config = {
       # """
       # Column level specifications for Florida DOR data
       # """
    "CO_NO": {'dtype' : str,
              'aggfunc': 'first',
              'na_value': 'unknown'},
    
    "PARCEL_ID": {'dtype' : str,
                  'aggfunc': 'first',
                  'na_value': 'unknown'},
    
    "DOR_UC": {'dtype' : str,
               'aggfunc': 'first',
               'na_value': 'unknown'},
    
    "JV": {'dtype' : float,
           'aggfunc': 'sum',
           'na_value': np.nan},
    
    "LND_VAL": {'dtype' : float,
                'aggfunc': 'sum',
                'na_value': np.nan},
    
    "LND_SQFOOT": {'dtype' : float,
                   'aggfunc': 'sum',
                   'na_value': np.nan},
    
    "NO_BULDNG": {'dtype' : 'Int64',
                  'aggfunc': 'sum',
                  'na_value': np.nan},
    
    "NO_RES_UNT": {'dtype' : 'Int64',
                    'aggfunc': 'sum',
                    'na_value': np.nan},
    
    "OWN_NAME": {'dtype' : str,
                 'aggfunc': 'first',
                 'na_value': 'unknown'},
    
    "CENSUS_BK": {'dtype' : str,
                  'aggfunc': 'first',
                  'na_value': 'unknown'},
    
    "TOT_LVG_AR": {'dtype' : float, 
                   'aggfunc': 'sum',
                   'na_value': np.nan},
    
    "EFF_YR_BLT": {'dtype' : 'Int64',
                    'aggfunc': 'sum',
                    'na_value': np.nan},
    
    "ACT_YR_BLT": {'dtype' : 'Int64',
                    'aggfunc': 'sum',
                    'na_value': np.nan},
}

fl_par_config_csv = {
       # """
       # Column level specifications for Florida DOR data
       # includes pd.na to deal with csv read nonsense
       # """
    "CO_NO": {'dtype' : str,
              'aggfunc': 'first',
              'na_value': 'unknown'},
    
    "PARCEL_ID": {'dtype' : str,
                  'aggfunc': 'first',
                  'na_value': 'unknown'},
    
    "DOR_UC": {'dtype' : str,
               'aggfunc': 'first',
               'na_value': 'unknown'},
    
    "JV": {'dtype' : float,
           'aggfunc': 'sum',
           'na_value': np.nan},
    
    "LND_VAL": {'dtype' : float,
                'aggfunc': 'sum',
                'na_value': np.nan},
    
    "LND_SQFOOT": {'dtype' : float,
                   'aggfunc': 'sum',
                   'na_value': np.nan},
    
    "NO_BULDNG": {'dtype' : 'Int64',
                  'aggfunc': 'sum',
                  'na_value': np.nan},
    
    "OWN_NAME": {'dtype' : str,
                 'aggfunc': 'first',
                 'na_value': 'unknown'},
    
    "CENSUS_BK": {'dtype' : str,
                  'aggfunc': 'first',
                  'na_value': 'unknown'},
    
    "TOT_LVG_AREA": {'dtype' : float, 
                   'aggfunc': 'sum',
                   'na_value': np.nan},
    
    "NO_RES_UNTS": {'dtype' : 'Int64',
                    'aggfunc': 'sum',
                    'na_value': np.nan},
    
    "EFF_YR_BLT": {'dtype' : 'Int64',
                    'aggfunc': 'sum',
                    'na_value': np.nan},
    
    "ACT_YR_BLT": {'dtype' : 'Int64',
                    'aggfunc': 'sum',
                    'na_value': np.nan},
}