# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 14:21:22 2022

@author: AZ7
"""

import re
import pandas as pd
import numpy as np

from rputils import dl_census
from core_config import * #TODO: is this right?

#TODO: docs for class methods

# %% Helper functions

def _check_breaks(breaks, config):
    '''
    Validate breaks provided for numeric reclassification of numeric ACS
    variables.

    Parameters
    ----------
    breaks : iterable of numerics, or None
        Break points for numeric reclassification (None if aliasing or a preset 
        reclassification is to be used instead).
    config : ACSConfig
        The config for the variable of interest.

    Raises
    ------
    ValueError
        If any break point is NOT possible according to the existing splits
        of the ACS data.

    Returns
    -------
    iterable of numerics, or None
        A copy of `breaks` is returned if all breaks are valid.

    '''
    if breaks is None:
        return breaks
    else:
        if config.reclass == True:
            if all(np.isin(breaks, config.lb)):
                return breaks
            else:
                raise ValueError("Invalid breaks provided; breaks must "\
                                 "be a subset of: "\
                                 "{', '.join(np.sort(np.unique(config.lb)))}")
        else:
            raise ValueError("Reclass not supported for this variable")

def _check_name(name, config):
    '''
    Validate name provided for aliasing or preset reclassification of ACS 
    variables.

    Parameters
    ----------
    name : str, or None
        Name of the aliasing or preset to use. Note that for all ACS downloads
        in `sam`, the aliasing option is "full", which returns all levels of
        the variable of interest. (None if a numeric reclassification
        is to be used instead).
    config : ACSConfig
        The config for the variable of interest.

    Raises
    ------
    ValueError
        If the name is NOT a reclassification option for the variable of
        interest.

    Returns
    -------
    str, or None
        A copy of `name` is returned if it is valid.

    '''
    if name is None or name in config.opts:
        return name
    else:
        raise ValueError("Invalid name; must be one of: "\
                         f"{', '.join(config._opts_)}")

def _combine_levels(df, idcol, config, breaks, name):
    '''
    Perform aliasing, preset reclassification, or numeric reclassification of
    ACS variables

    Parameters
    ----------
    df : pandas DataFrame
        df output of `rputils.download.dl_census`.
    idcol : str
        Unique ID column in `df` (starts with "GEOID").
    config : ACSConfig
        Config for the variable represented in `df`.
    breaks : iterable of numerics, or None
        Break points for numeric reclassification. One of `breaks` and `name` 
        must be provided; the other must be None.
    name : TYPE, optional
        Name of the aliasing or preset to use. Note that for all ACS downloads
        in `sam`, the aliasing option is "full", which returns all levels of
        the variable of interest. One of `breaks` and `name` must be provided; 
        the other must be None.

    Returns
    -------
    pandas.DataFrame
        Aliased or reclassified ACS data from `df`.

    '''
    if breaks is not None and name is None:
        dt = df.pivot(index=idcol,
                      columns="variable",
                      values="estimate")
        dt = dt.reset_index().drop(columns="variable")
        pref = df.alias.iloc[0].split("_")[0]
        breaks = [0] + np.sort(breaks).tolist()  + [np.inf]
        cols = [idcol]
        for i in np.arange(len(breaks)-1):
            l = breaks[i]
            u = breaks[i+1]
            if u == np.inf: 
                col = f"{pref}_{l}p"
            else:
                if u-l == 1:
                    col = f"{pref}_{l}"
                else:
                    col = f"{pref}_{l}_{u}"
            idx = config.index[np.logical_and(config.lb >= l, 
                                              config.lb < u)].tolist()
            dt[col] = dt[idx].sum(axis=1)
            cols.append(col)
        dt = dt[cols]
    elif breaks is None and name is not None:
        cfg = config.reset_index().rename(columns={"index":"variable"})
        cfg = cfg[["variable",name]]
        dt = df.merge(cfg, on="variable", how="inner")
        dt = dt.groupby([idcol,name])[["estimate"]].sum().reset_index()
        dt = dt.pivot_wider(index=idcol, columns=name, value="estimate")
        dt = dt.reset_index().drop(columns=name)
    else:
        raise ValueError("One of breaks and name must be provided, and "\
                         "the other must be None")
    return dt

def _discrete_processing(state, year, county, geography, config, name):
    '''
    Download ACS data, and perform aliasing or preset reclassification for
    discrete ACS variables

    Parameters
    ----------
    state : str
        State for the data; passed to `dl_census`.
    year : int
        Year for the data; passed to `dl_census`.
    county : str, iterable of str, or None
        County or counties for the data, if any; passed to `dl_census`
    geography : str
        Census geography for the data; passed to `dl_census`
    config : ACSConfig
        Config for the variable of interest
    name : str
        Name of the aliasing or preset to use. Note that for all ACS downloads
        in `sam`, the aliasing option is "full", which returns all levels of
        the variable of interest.

    Returns
    -------
    pd.DataFrame
        Aliased or reclassified ACS data from `df`.

    '''
    name = _check_name(name, config)
    df = dl_census("acs", geography=geography,
                   table=config, year=year,
                   state=state, county=county)
    idcol = [c for c in df.columns if bool(re.search("^GEOID",c))][0]
    tab = _combine_levels(df, idcol=idcol, config=config, 
                          breaks=None, name=name)
    return tab
    
def _numeric_processing(state, year, county, geography, config, breaks, name):
    '''
    Download ACS data, and perform aliasing or numeric reclassification for
    "numeric" ACS variables

    Parameters
    ----------
    state : str
        State for the data; passed to `dl_census`.
    year : int
        Year for the data; passed to `dl_census`.
    county : str, iterable of str, or None
        County or counties for the data, if any; passed to `dl_census`
    geography : str
        Census geography for the data; passed to `dl_census`
    config : ACSConfig
        Config for the variable of interest
    breaks : iterable of numerics, or None
        Break points for numeric reclassification. One of `breaks` and `name` 
        must be provided; the other must be None.
    name : str, or None
        Name of the aliasing or preset to use. Note that for all ACS downloads
        in `sam`, the aliasing option is "full", which returns all levels of
        the variable of interest. One of `breaks` and `name` must be provided;
        the other must be None.

    Returns
    -------
    pd.DataFrame
        Aliased or reclassified ACS data from `df`.

    '''
    breaks = _check_breaks(breaks, config)
    name = _check_name(name, config)
    df = dl_census("acs", geography=geography,
                   table=config, year=year,
                   state=state, county=county)
    idcol = [c for c in df.columns if bool(re.search("^GEOID",c))][0]
    tab = _combine_levels(df, idcol=idcol, config=config, 
                          breaks=breaks, name=name)
    return tab
    
# %% Class

class ACS(pd.DataFrame):
    def __init__(self, df, univ):
        super().__init__(df)
        self._universe_ = univ
    
    def to_csv(self, save_path):
        self.to_csv(save_path)
        
    @classmethod
    def sex(cls, state, year, county=None, geography="block group", 
            name="full"):
        cfg = _SEX_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def age(cls, state, year, county=None, geography="block group", 
            breaks=None, name="full"):
        cfg = _AGE_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def hh_income(cls, state, year, county=None, geography="block group",
                  breaks=None, name="full"):
        cfg = _INCOME_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def ratio_of_income_to_poverty_level(cls, state, year, county=None, geography="block group", 
                                         breaks=None, name="full"):
        cfg = _RIP_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def hh_vehicles(cls, state, year, county=None, geography="block group", 
                    breaks=None, name="full"):
        cfg = _VEHICLES_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def tenure(cls, state, year, county=None, geography="block group", 
               name="full"):
        cfg = _TENURE_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def disability_status(cls, state, year, county=None, geography="block group", 
                          name="full"):
        if geography == "block group":
            cfg = _DISABILITY_BG_CONFIG_
        else:
            cfg = _DISABILITY_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def hh_size(cls, state, year, county=None, geography="block group", 
            breaks=None, name="full"):
        cfg = _SIZE_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def hh_workers(cls, state, year, county=None, geography="block group", 
                   breaks=None, name="full"):
        if geography == "block group":
            cfg = _WORKERS_BG_CONFIG_
        else:
            cfg = _WORKERS_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def education(cls, state, year, county=None, geography="block group", 
                  name="full"):
        if geography == "block group":
            cfg = _EDUCATION_BG_CONFIG_
        else:
            cfg = _EDUCATION_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def race(cls, state, year, county=None, geography="block group", 
             name="full"):
        cfg = _RACE_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def ethnicity(cls, state, year, county=None, geography="block group", 
                  name="full"):
        cfg = _ETHNICITY_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def minority_status(cls, state, year, county=None, geography="block group", 
            name="full"):
        cfg = _MINORITY_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def mode_share(cls, state, year, county=None, geography="block group", 
                   name="full"):
        cfg = _MODE_SHARE_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        tab = tab.drop(columns="")
        for c in tab.columns:
            if bool(re.search("^GEOID",c)) or c == "total":
                pass
            else:
                tab[c] = tab[c] / tab["total"]
        return cls(tab, univ=cfg._universe_)
    
    
        
            
                
                
        