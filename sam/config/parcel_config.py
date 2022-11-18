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
    
    "NO_BULDNG": {'dtype' : int,
                  'aggfunc': 'sum',
                  'na_value': np.nan},
    
    "NO_RES_UNT": {'dtype' : int,
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
    
    "NO_RES_UNT": {'dtype' : int,
                    'aggfunc': 'sum',
                    'na_value': np.nan},
    
    "EFF_YR_BLT": {'dtype' : int,
                    'aggfunc': 'sum',
                    'na_value': np.nan},
    
    "ACT_YR_BLT": {'dtype' : int,
                    'aggfunc': 'sum',
                    'na_value': np.nan},
}