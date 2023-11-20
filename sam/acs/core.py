# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 14:21:22 2022

@author: Aaron Weinstock
"""

import re
import pandas as pd
import numpy as np
import sam.config.acs_config as acs_cfg

from sam.download.census import dl_census
from sam.config.helper_functions import create_geo_dict

# TODO: rent and value methods
# TODO: meta data handling (also lodes)
# Helper functions
def _check_breaks(config, breaks=None):
    """
    Validate breaks provided for numeric reclassification of numeric ACS
    variables.

    Parameters
    ----------
    config : ACSConfig
        The config for the variable of interest.
    breaks : iterable of numerics, optional
        Break points for numeric reclassification (None if aliasing or a preset
        reclassification is to be used instead). Breaks will be assessed
        in rolling pairs as `>=, <`.

    Raises
    ------
    ValueError
        If any break point is NOT possible according to the existing splits
        of the ACS data.

    Returns
    -------
    iterable of numerics, or None
        A copy of `breaks` is returned if all breaks are valid.

    """
    if breaks is None:
        return breaks
    else:
        if config._reclass_ == True:
            if all(np.isin(breaks, config.lb)):
                return breaks
            else:
                raise ValueError(
                    "Invalid breaks provided; breaks must "
                    "be a subset of: "
                    "{', '.join(np.sort(np.unique(config.lb)))}"
                )
        else:
            raise ValueError("Reclass not supported for this variable")


# TODO fix break bug


def _check_name(config, name=None):
    """
    Validate name provided for aliasing or preset reclassification of ACS
    variables.

    Parameters
    ----------
    config : ACSConfig
        The config for the variable of interest.
    name : str, or None
        Name of the aliasing or preset to use. Note that for all ACS downloads
        in `sam`, the aliasing option is "full", which returns all levels of
        the variable of interest. (None if a numeric reclassification
        is to be used instead).

    Raises
    ------
    ValueError
        If the name is NOT a reclassification option for the variable of
        interest.

    Returns
    -------
    str, or None
        A copy of `name` is returned if it is valid.

    """
    if name is None or name in config.opts:
        return name
    else:
        raise ValueError("Invalid name; must be one of: " f"{', '.join(config._opts_)}")


def _combine_levels(df, idcol, config, breaks=None, name="full"):
    """
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
        in rolling pairs as `>=, <`. The default is None.
    name : TYPE, optional
        Name of the aliasing or preset to use. Note that for all ACS downloads
        in `sam`, the aliasing option is "full", which returns all levels of
        the variable of interest. One of `breaks` and `name` must be provided;
        the other must be None. The default is "full", indicating aliasing
        will be used.

    Returns
    -------
    pandas.DataFrame
        Aliased or reclassified ACS data from `df`.

    """
    if breaks is not None and name is None:
        dt = df.pivot(index=idcol, columns="variable", values="estimate")
        dt = dt.reset_index().drop(columns="variable")
        pref = df.alias.iloc[0].split("_")[0]
        breaks = [0] + np.sort(breaks).tolist() + [np.inf]
        cols = [idcol]
        for i in np.arange(len(breaks) - 1):
            l = breaks[i]
            u = breaks[i + 1]
            if u == np.inf:
                col = f"{pref}_{l}p"
            else:
                if u - l == 1:
                    col = f"{pref}_{l}"
                else:
                    col = f"{pref}_{l}_{u}"
            idx = config._df_.index[
                np.logical_and(config._df_.lb >= l, config.lb < u)
            ].tolist()
            dt[col] = dt[idx].sum(axis=1)
            cols.append(col)
        dt = dt[cols]
    elif breaks is None and name is not None:
        cfg = config._df_.reset_index().rename(columns={"index": "variable"})
        cfg = cfg[["variable", name]]
        dt = df.merge(cfg, on="variable", how="inner")
        dt = dt.groupby([idcol, name])[["estimate"]].sum().reset_index()
        dt = dt.pivot(index=idcol, columns=name, values="estimate")
        dt = dt.reset_index()  # .drop(columns=name)
    else:
        raise ValueError(
            "One of breaks and name must be provided, and " "the other must be None"
        )
    return dt


def _discrete_processing(geography, config, geoid, year, name="full"):
    """
    Download ACS data, and perform aliasing or preset reclassification for
    discrete ACS variables

    Parameters
    ----------
    geography : str
        Census geography for the data; passed to `dl_census`.
    config : ACSConfig
        Config for the variable of interest
    geoid : str or int or list of either.
        5 digit census FIPS GEOID; passed to `dl_census`.
    year : int
        Year for the data; passed to `dl_census`.
    name : str
        Name of the aliasing or preset to use. Note that for all ACS downloads
        in `sam`, the aliasing option is "full", which returns all levels of
        the variable of interest. The default is "full", indicating aliasing
        will be used.

    Returns
    -------
    pd.DataFrame
        Aliased or reclassified ACS data from `df`.

    """
    # create a dict of state fips and the county fips in each state
    # geoid=['10003', '24015', '42029', '42015']
    geo_dict = create_geo_dict(geoids=geoid)
    
    # loop over the dicts pulling only the correct counties
    tbl_out = []
    for state in geo_dict.keys():
        df = dl_census(
            "acs",
            geography=geography,
            table=config._table_,
            year=year,
            state=state,
            county=geo_dict[state]
        )
        idcol = [c for c in df.columns if bool(re.search("^GEOID", c))][0]
        tbl = _combine_levels(df, idcol=idcol, config=config, 
                              breaks=None, name=name)
        tbl_out.append(tbl)
        
    tbl = pd.concat(tbl_out)
    return tbl


def _numeric_processing(
    geography, config, geoid, year, breaks=None, name="full"
):
    """
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
        in rolling pairs as `>=, <`. The default is None.
    name : str, or None
        Name of the aliasing or preset to use. Note that for all ACS downloads
        in `sam`, the aliasing option is "full", which returns all levels of
        the variable of interest. One of `breaks` and `name` must be provided;
        the other must be None. The default is "full", indicating aliasing
        will be used.

    Returns
    -------
    pd.DataFrame
        Aliased or reclassified ACS data from `df`.

    """
    # create a dict of state fips and the county fips in each state
    # geoid=['10003', '24015', '42029', '42015']
    geo_dict = create_geo_dict(geoids=geoid)
    
    # loop over the dicts pulling only the correct counties
    tbl_out = []
    breaks = _check_breaks(config=config, breaks=breaks)
    # name = _check_name(name, config)
    dtbl_out = []
    for state in geo_dict.keys():
        df = dl_census(
            "acs",
            geography=geography,
            table=config._table_,
            year=year,
            state=state,
            county=geo_dict[state]
        )
        idcol = [c for c in df.columns if bool(re.search("^GEOID", c))][0]
        tbl = _combine_levels(df, idcol=idcol, config=config, 
                              breaks=breaks, name=name)
        tbl_out.append(tbl)
        
    tbl = pd.concat(tbl_out)
    return tbl

# Class
@pd.api.extensions.register_dataframe_accessor("acs")
class ACS:
    """
    Download ACS data
    """

    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def sex(year, geoid, geography="block group", name="full"):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._SEX_CONFIG_
        tbl = _discrete_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
        )
        return tbl

    def age(
        year, geoid, geography="block group", breaks=None, name="full"
    ):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._AGE_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def age_by_sex(
        year, geoid, geography="block group", breaks=None, name="full"
    ):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._AGE_BY_SEX_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def hh_income(
        year, geoid , geography="block group", breaks=None, name="full"
    ):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._INCOME_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def ratio_of_income_to_poverty_level(
        year, geoid , geography="block group", breaks=None, name="full"
    ):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._RIP_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def hh_vehicles(
        year, geoid , geography="block group", breaks=None, name="full"
    ):
        """
        Download ACS household vehicles' data (universe: total households).

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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._VEHICLES_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def tenure(year, geoid , geography="block group", name="full"):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._TENURE_CONFIG_
        tbl = _discrete_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
        )
        return tbl

    def disability_status(
        year, geoid , geography="block group", name="full"
    ):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        if geography == "block group":
            cfg = acs_cfg._DISABILITY_BG_CONFIG_
        else:
            cfg = acs_cfg._DISABILITY_CONFIG_
        tbl = _discrete_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
        )
        return tbl

    def hh_size(
        year, geoid , geography="block group", breaks=None, name="full"
    ):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._SIZE_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def hh_workers(
        year, geoid , geography="block group", breaks=None, name="full"
    ):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        if geography == "block group":
            cfg = acs_cfg._WORKERS_BG_CONFIG_
        else:
            cfg = acs_cfg._WORKERS_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def education(year, geoid , geography="block group", name="full"):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        if geography == "block group":
            cfg = acs_cfg._EDUCATION_BG_CONFIG_
        else:
            cfg = acs_cfg._EDUCATION_CONFIG_
        tbl = _discrete_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
        )
        return tbl

    def race(year, geoid , geography="block group", name="full"):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._RACE_CONFIG_
        tbl = _discrete_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
        )
        return tbl

    def ethnicity(year, geoid , geography="block group", name="full"):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._ETHNICITY_CONFIG_
        tbl = _discrete_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
        )
        return tbl

    def minority_status(year, geoid , geography="block group", name="full"):
        """
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
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._MINORITY_CONFIG_
        tbl = _discrete_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
        )
        return tbl

    def mode_share(year, geoid , geography="block group", name="full"):
        """
        Download ACS mode share data (universe: 16+ working population).

        Parameters
        ----------
        see `sam.acs._discrete_processing`

        Notes
        -----
        Options include:
            1. `name = "full"`: all car/truck/van (car), drove alone (car_1),
            all carpool (car_2p), 2-person carpool (car_2p_2), 3-person carpool
            (car_2p_3), 4-person carpool (car_2p_4), 5- or 6-person carpool
            (car_2p_56), 7+-person carpool (car_2p_7p), all public
            transportation (tran), bus (tran_bus), subway or elevated rail
            (tran_ser), long-distance train or commuter rail (tran_ldtcr),
            light rail/streetcar/trolley (tran_lrst), ferry (tran_ferry),
            taxicab (taxi), motorcycle (motorcycle), bike (bike), walk (walk),
            other mode of transportation (other), worked from home (wfh)
            2. `name = "basic"`: car/truck/van/carpool/motorcycle (auto),
            any public transportation (transit), bike or walk (nonmot), taxi
            or other mode (other), worked from home (wfh)
        All columns will be represented as shares. Regardless of the choice of
        `name`, an additional column "trips" will be provided to indicated the
        total number of commutes. This column may be multiplied by a shares
        column to return the number of trips for that mode.

        Returns
        -------
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._MODE_SHARE_CONFIG_
        tbl = _discrete_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
        )
        # tbl = tbl.drop(columns="")
        for c in tbl.columns:
            if bool(re.search("^GEOID", c)) or c == "trips":
                pass
            else:
                tbl[c] = tbl[c] / tbl["trips"]
        return tbl

    def totals(year, geoid , geography="block group", name="full"):
        """
        Download ACS total population, households, and housing units data

        This will download 3 separate tables for each statistic, and bind
        them all into a singular table of totals

        Parameters
        ----------
        see `sam.acs._discrete_processing`

        Notes
        -----
        Options include:
            1. `name = "full"`: total population (pop), total households (hh),
            total housing units (hu)

        Returns
        -------
        ACS (subclass of pd.DataFrame)

        """
        cfgs = [
            acs_cfg._TOT_POP_CONFIG_,
            acs_cfg._TOT_HH_CONFIG_,
            acs_cfg._TOT_HU_CONFIG_,
        ]
        tbl = [
            _discrete_processing(
                geography=geography,
                config=cfg,
                geoid=geoid,
                year=year,
                name=name,
            )
            for cfg in cfgs
        ]
        idcol = [c for c in tbl[0].columns if bool(re.search("^GEOID", c))][0]
        tbl = [df.set_index(idcol) for df in tbl]
        tbl = pd.concat(tbl, axis=1).reset_index()
        return tbl

    def rent(
        year, geoid , geography="block group", breaks=None, name="full"
    ):
        """
        Download ACS rent data (universe: Renter-occupied housing units).

        Parameters
        ----------
        see `sam.acs._numeric_processing`

        Notes
        -----
        Options include:
            1. `name = "full"`: full names for bins
            2. `breaks = [...]`: only lower bound of bin

        Returns
        -------
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._RENT_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def value(
        year, geoid , geography="block group", breaks=None, name="full"
    ):
        """
        Download ACS housing value data (universe: Owner-occupied Housing Units).

        Parameters
        ----------
        see `sam.acs._numeric_processing`

        Notes
        -----
        Options include:
            1. `name = "full"`: full names for bins
            2. `breaks = [...]`: only lower bound of bin

        Returns
        -------
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._VALUE_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl

    def cost(
        year, geoid , geography="block group", breaks=None, name="full"
    ):
        """
        Download ACS housing cost data (universe: Owner-occupied Housing Units).

        Parameters
        ----------
        see `sam.acs._numeric_processing`

        Notes
        -----
        Options include:
            1. `name = "full"`: full names for bins
            2. `breaks = [...]`: only lower bound of bin

        Returns
        -------
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._COST_CONFIG_
        tbl = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=name,
            breaks=breaks,
        )
        return tbl
    
    # def migration(
    #     year, geoid , geography="tract", breaks=None, name="full"
    # ):
    #     """
    #     Download ACS housing cost data (universe: Owner-occupied Housing Units).

    #     Parameters
    #     ----------
    #     see `sam.acs._numeric_processing`

    #     Notes
    #     -----
    #     Options include:
    #         1. `name = "full"`: full names for bins
    #         2. `breaks = [...]`: only lower bound of bin

    #     Returns
    #     -------
    #     ACS (subclass of pd.DataFrame)

    #     """
    #     cfg = acs_cfg._MIGRATION_CONFIG_
    #     tbl = _numeric_processing(
    #         geography=geography,
    #         config=cfg,
    #         geoid=geoid,
    #         year=year,
    #         name=name,
    #         breaks=breaks,
    #     )
    #     return tbl
    
    def year_moved(year, geoid, geography="block group"):
        """
        Download ACS year moved in data (universe: total households).

        Parameters
        ----------
        see `sam.acs._discrete_processing`

        Notes
        -----
        Options include:
            1. `name = "full"`: own, rent

        Returns
        -------
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._YEAR_MOVED_IN_CONFIG_
        tbl_cur = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=str(year),
        )
        #TODO add the cross walk for 2010 to 2020 geo
        tbl_cur = tbl_cur.rename(
            columns={col: f'{col}_from_{year}' 
                     for col in tbl_cur.columns if col != 'GEOID'}
        )
        
        tbl_pre = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year-1,
            name=str(year-1),
        )
        
        tbl_pre = tbl_pre.rename(
            columns={col: f'{col}_from_{year - 1}' 
                     for col in tbl_pre.columns if col != 'GEOID'}
        )
        
        if year == 2020:
            from sam.config.acs_config import xw_2010_to_2020
            xw_2010_to_2020['src_pct'] = (xw_2010_to_2020['AREALAND_PART'] / 
                                        xw_2010_to_2020['AREALAND_BLKGRP_10'])

            xw_2010_to_2020['GEOID_BLKGRP_20'] = xw_2010_to_2020[
                'GEOID_BLKGRP_20'].astype(str)
            xw_2010_to_2020['GEOID_BLKGRP_10'] = xw_2010_to_2020[
                'GEOID_BLKGRP_10'].astype(str)
            xw_2010_to_2020 = xw_2010_to_2020.loc[
                xw_2010_to_2020['GEOID_BLKGRP_20'].isin(tbl_cur['GEOID'])
                ]
            keep_cols = tbl_pre.columns
            math_cols = [col for col in keep_cols if col != 'GEOID']

            tbl_pre = tbl_pre.merge(
                xw_2010_to_2020[['GEOID_BLKGRP_20', 'GEOID_BLKGRP_10', 'src_pct']],
                left_on='GEOID', right_on='GEOID_BLKGRP_10'
                )

            for col in math_cols:
                tbl_pre[col] = np.round(tbl_pre[col] * tbl_pre['src_pct'], 
                                        decimals=0)
                
                
            tbl_pre.drop(columns=['src_pct', 'GEOID', 'GEOID_BLKGRP_10'], 
                         inplace=True)
            tbl_pre.rename(columns={'GEOID_BLKGRP_20': 'GEOID'}, 
                           inplace=True)

            tbl_pre = tbl_pre.groupby('GEOID').agg('sum').reset_index()
        
        tbl = tbl_cur.merge(tbl_pre)
        return tbl
    
    def year_built(year, geoid , geography="block group"):
        """
        Download ACS year built in data (universe: total households).

        Parameters
        ----------
        see `sam.acs._discrete_processing`

        Notes
        -----
        Options include:
            1. `name = "full"`: own, rent

        Returns
        -------
        ACS (subclass of pd.DataFrame)

        """
        cfg = acs_cfg._YEAR_BLT__
        tbl_cur = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year,
            name=str(year),
        )
        #TODO add the cross walk for 2010 to 2020 geo
        tbl_cur = tbl_cur.rename(
            columns={col: f'{col}_from_{year}' 
                     for col in tbl_cur.columns if col != 'GEOID'}
        )
        
        tbl_pre = _numeric_processing(
            geography=geography,
            config=cfg,
            geoid=geoid,
            year=year-1,
            name=str(year-1),
        )
        
        tbl_pre = tbl_pre.rename(
            columns={col: f'{col}_from_{year - 1}' 
                     for col in tbl_pre.columns if col != 'GEOID'}
        )
        
        if year == 2020:
            from sam.config.acs_config import xw_2010_to_2020
            xw_2010_to_2020['src_pct'] = (xw_2010_to_2020['AREALAND_PART'] / 
                                        xw_2010_to_2020['AREALAND_BLKGRP_10'])

            xw_2010_to_2020['GEOID_BLKGRP_20'] = xw_2010_to_2020[
                'GEOID_BLKGRP_20'].astype(str)
            xw_2010_to_2020['GEOID_BLKGRP_10'] = xw_2010_to_2020[
                'GEOID_BLKGRP_10'].astype(str)
            xw_2010_to_2020 = xw_2010_to_2020.loc[
                xw_2010_to_2020['GEOID_BLKGRP_20'].isin(tbl_cur['GEOID'])
                ]
            keep_cols = tbl_pre.columns
            math_cols = [col for col in keep_cols if col != 'GEOID']

            tbl_pre = tbl_pre.merge(
                xw_2010_to_2020[['GEOID_BLKGRP_20', 'GEOID_BLKGRP_10', 'src_pct']],
                left_on='GEOID', right_on='GEOID_BLKGRP_10'
                )

            for col in math_cols:
                tbl_pre[col] = np.round(tbl_pre[col] * tbl_pre['src_pct'], 
                                        decimals=0)
                
                
            tbl_pre.drop(columns=['src_pct', 'GEOID', 'GEOID_BLKGRP_10'], 
                         inplace=True)
            tbl_pre.rename(columns={'GEOID_BLKGRP_20': 'GEOID'}, 
                           inplace=True)

            tbl_pre = tbl_pre.groupby('GEOID').agg('sum').reset_index()
        
        tbl = tbl_cur.merge(tbl_pre)
        return tbl
    
if __name__ == "__main__":
    pass