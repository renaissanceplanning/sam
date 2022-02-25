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

#TODO: total method
#TODO: race and value methods

# %% Helper functions

def _check_breaks(breaks, config):
    '''
    Validate breaks provided for numeric reclassification of numeric ACS
    variables.

    Parameters
    ----------
    breaks : iterable of numerics, or None
        Break points for numeric reclassification (None if aliasing or a preset 
        reclassification is to be used instead). Breaks will be assessed
        in rolling pairs as `>=, <`.
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
        must be provided; the other must be None. Breaks will be assessed
        in rolling pairs as `>=, <`.
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
        must be provided; the other must be None. Breaks will be assessed
        in rolling pairs as `>=, <`.
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
        '''
        Download ACS sex data (universe: total population).

        Parameters
        ----------
        see `sam.acs._discrete_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: male, female

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _SEX_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def age(cls, state, year, county=None, geography="block group", 
            breaks=None, name="full"):
        '''
        Download ACS age data (universe: total population).

        Parameters
        ----------
        see `sam.acs._numeric_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: <=4, 5-9, 10-14, 15-17, 18-19, 20, 21, 22-24,
            25-29, 30-34, 35-39, 40-44, 45-49, 50-54, 55-59, 60-61, 62-64,
            65-66, 67-69, 70-74, 75-79, 80-84, >=85
            2. `breaks = [...]`: valid break points include 5, 10, 15, 18, 20,
            21, 22, 25, 30, 35, 40, 45, 50, 55, 60, 62, 65, 67, 70, 75, 80,
            and 85

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _AGE_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def hh_income(cls, state, year, county=None, geography="block group",
                  breaks=None, name="full"):
        '''
        Download ACS household income data (universe: total households).

        Parameters
        ----------
        see `sam.acs._numeric_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: <10, [10,15), [15,20), [20,25), [25,30), 
            [30,35), [35,40), [40,45), [45,50), [50,60), [60,75), [75,100),
            [100,125), [125,150), [150,200), >=200 (in thousands)
            2. `breaks = [...]`: valid break points include 10, 15, 20, 25, 30,
            35, 40, 45, 50, 60, 75, 100, 125, 150, and 200

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _INCOME_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def ratio_of_income_to_poverty_level(cls, state, year, county=None, geography="block group", 
                                         breaks=None, name="full"):
        '''
        Download ACS ratio of income to poverty level data (universe:
        population for whom poverty status can be determined).

        Parameters
        ----------
        see `sam.acs._numeric_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: <0.5, [0.5,1), [1,1.25), [1.25,1.5),
            [1.5,1.85), [1.85,2), >=2
            2. `breaks = [...]`: valid break points include 0.5, 1, 1.25, 1.5,
            1.85, and 2

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _RIP_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def hh_vehicles(cls, state, year, county=None, geography="block group", 
                    breaks=None, name="full"):
        '''
        Download ACS household vehicles data (universe: total households).

        Parameters
        ----------
        see `sam.acs._numeric_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: 0, 1, 2, 3, 4, >=5
            2. `breaks = [...]`: valid break points include 0, 1, 2, 3, 4, 
            and 5

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _VEHICLES_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def tenure(cls, state, year, county=None, geography="block group", 
               name="full"):
        '''
        Download ACS tenure data (universe: total households).

        Parameters
        ----------
        see `sam.acs._discrete_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: own, rent

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _TENURE_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def disability_status(cls, state, year, county=None, geography="block group", 
                          name="full"):
        '''
        Download ACS disability status data (universe for block group level
        data: civilian 18+ population for whom poverty status can be 
        determined; universe for higher level data: civilian 
        non-institutionalized population).

        Parameters
        ----------
        see `sam.acs._discrete_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: with a disability (yes), without a
            disability (no)

        Returns
        -------
        ACS
            table of ACS data

        '''
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
        '''
        Download ACS household size data (universe: total households.

        Parameters
        ----------
        see `sam.acs._numeric_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: 0, 1, 2, 3, 4, 5, 6, >=7
            2. `breaks = [...]`: valid break points include 0, 1, 2, 3, 4, 5,
            6, and 7

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _SIZE_CONFIG_
        tab = _numeric_processing(state=state, year=year, county=county,
                                  geography=geography, config=cfg, 
                                  breaks=breaks, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def hh_workers(cls, state, year, county=None, geography="block group", 
                   breaks=None, name="full"):
        '''
        Download ACS household number of workers data (universe for block
        group level data: family households; universe for higher level data: 
        total households).

        Parameters
        ----------
        see `sam.acs._numeric_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: 0, 1, 2, >=3
            2. `breaks = [...]`: valid break points include 0, 1, 2, and 3

        Returns
        -------
        ACS
            table of ACS data

        '''
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
        '''
        Download ACS educational attainment data (universe for block group
        level data: 25+ population; universe for higher level data: 18+
        population).

        Parameters
        ----------
        see `sam.acs._discrete_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: <9th grade (lths), 9th-12th grade (shs), 
            high school graduate or equivalency (hs), some college but no
            degree (scnd), Associate's degree (assc), Bachelor's degree (bach),
            graduate or professional degree (gradprof)
            2. `name = "basic": <12th grade (lths), high school graduate or
            equivalency (hs), some college or Associate's degree (scndassc),
            Bachelor's degree (bach), graduate or professional 
            degree (gradprof)

        Returns
        -------
        ACS
            table of ACS data

        '''
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
        '''
        Download ACS race data (universe: total population).

        Parameters
        ----------
        see `sam.acs._discrete_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: white (white), black (black), American Indian
            or Alaska native (aian), asian (asian), native Hawaiian or other
            Pacific islander (nhopi), other (other), two or more (twoplus)

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _RACE_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def ethnicity(cls, state, year, county=None, geography="block group", 
                  name="full"):
        '''
        Download ACS ethnicity data (universe: total population).

        Parameters
        ----------
        see `sam.acs._discrete_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: hispanic (hisp), non-hispanic (nonhisp)

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _ETHNICITY_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
        return cls(tab, univ=cfg._universe_)
    
    @classmethod
    def minority_status(cls, state, year, county=None, geography="block group", 
            name="full"):
        '''
        Download ACS minority status data (universe: total population).

        Parameters
        ----------
        see `sam.acs._discrete_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: non-white OR hispanic (mnty), white AND 
            non-hispanic (nonmnty)

        Returns
        -------
        ACS
            table of ACS data

        '''
        cfg = _MINORITY_CONFIG_
        tab = _discrete_processing(state=state, year=year, county=county,
                                   geography=geography, config=cfg, name=name)
        return cls(tab, univ=cfg._universe_)
    
    # TODO: complete docs
    @classmethod
    def mode_share(cls, state, year, county=None, geography="block group", 
                   name="full"):
        '''
        Download ACS mode share data (universe: 16+ working population).

        Parameters
        ----------
        see `sam.acs._discrete_processing`
        
        Notes
        -----
        Options include:
            1. `name = "full"`: car (car) ...

        Returns
        -------
        ACS
            table of ACS data

        '''
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
    
    
        
            
                
                
        