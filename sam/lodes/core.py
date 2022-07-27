# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 15:42:42 2022

@author: Aaron Weinstock
"""

import re
# import us
import numpy as np
import pandas as pd

from rputils.download.census import dl_lodes, dl_xwalk

# Helper functions
def _dlfm_lodes_ac(file, state, year, idcol):
    """
    DownLoad and ForMat an LODES area characteristics file.

    Parameters
    ----------
    file : str
        File type: either "rac" or "wac"; passed to `dl_lodes`.
    state : str
        2-letter postal code for a chosen state; passed to `dl_lodes`.
    year : int
        Year for the data; passed to `dl_lodes`.
    idcol : str
        Block ID column in the file.

    Returns
    -------
    pd.DataFrame

    """
    df = dl_lodes(file=file, ST=state, TYPE="JT00", 
                  YEAR=year, SEG="S000", PART=None)
    df[idcol] = df[idcol].astype(str)
    df = df.drop(columns="createdate")
    return df

@pd.api.extensions.register_dataframe_accessor("lodes")
class lodes:
    """
    Download LODES data
    """
    def __init__(self, pandas_obj):
        self._obj = pandas_obj
        
    # @property
    # def datastate(self):
    #     return self.__datastate__
        
    def xwalk(state):
        """
        Download the geography crosswalk for a state.
        Parameters
        ----------
        state : str
            2-letter postal code for a chosen state.
        Returns
        -------
        pd.DataFrame
        """
        df = dl_xwalk(ST=state)
        df = df.drop(columns=["blklatdd", "blklondd", "createdate"])
        # df.lodes.__dict__['__datastate__'] = state
        return df
    
    def rac(state, year):
        """
        Download LODES residence area characteristics data (for all jobs in all
        segments)

        Parameters
        ----------
        See `sam.lodes._dlfm_lodes_ac`

        Returns
        -------
        LODES (subclass of pd.DataFrame)

        """
        df = _dlfm_lodes_ac(file="rac", state=state, year=year, idcol="h_geocode")
        # df.lodes.__dict__['__datastate__'] = state
        # df.lodes.__dict__['__datayear__'] = year
        return df

    def wac(state, year):
        """
        Download LODES workplace area characteristics data (for all jobs in all
        segments)

        Parameters
        ----------
        See `sam.lodes._dlfm_lodes_ac`

        Returns
        -------
        LODES (subclass of pd.DataFrame)

        """
        df = _dlfm_lodes_ac(file="wac", state=state, year=year, idcol="w_geocode")
        # df.lodes.__dict__['__datastate__'] = state
        # df.lodes.__dict__['__datayear__'] = year
        return df

    def od(state, year):
        """
        Download LODES origin-destiantion data (for all jobs in all segments)

        Parameters
        ----------
        state : str
            2-letter postal code for a chosen state.
        year : int
            Year for the data.

        Returns
        -------
        LODES (subclass of pd.DataFrame)

        """
        main = dl_lodes(
            file="od", ST=state, TYPE="JT00", YEAR=year, SEG=None, PART="main"
        )
        aux = dl_lodes(
            file="od", ST=state, TYPE="JT00", YEAR=year, SEG=None, PART="aux"
        )
        df = pd.concat([main, aux])
        df["h_geocode"] = df.h_geocode.astype(str)
        df["w_geocode"] = df.w_geocode.astype(str)
        df = df.drop(columns="createdate")
        # df.lodes.__dict__['__datastate__'] = state
        # df.lodes.__dict__['__datayear__'] = year
        return df

    # TODO: set this as LODES? or is it already?
    def aggregate(self, XWalk, to, keepname=False):
        """
        Aggregate LODES data up from the block level to a higher geographic
        level.

        Parameters
        ----------
        XWalk : XWalk
            The geography crosswalk for the state of the LODES data.
        to : str
            Geography to which to aggregate; must match the XWalk column name
            for this geography (e.g. "block group"-->"bgrp").
        keepname : bool
            Should the name of the aggregate geography be retained? Helpful
            for aggregtions to areas commonly referred to by name, e.g.
            counties, but not to much for places commonly referred to by ID,
            e.g. tracts. The default is False, in which case only the ID will
            be retained.

        Returns
        -------
        pd.DataFrame

        """
        # TODO add handleing for fips to string (fix bug with OD)
        # lodes_st = us.states.lookup(self.__datastate__)
        # XWalk_st = us.states.lookup(XWalk.lodes.__datastate__)
        
        # if lodes_st == XWalk_st:
        #     pass
        # else:
        #     raise ValueError(
        #         "LODES state != XWalk state; "
        #         f"{lodes_st} and {XWalk_st}"
        #     )
        agg_opts = [
            c
            for c in XWalk.columns
            if np.logical_and(
                bool(re.search("blk", c)) == False, 
                bool(re.search("name$", c)) == False
            )
        ]
        if to in agg_opts:
            pass
        else:
            raise ValueError(
                f"{to} is not a valid aggregation geography; "
                f"must be one of {', '.join(agg_opts)}"
            )
        xwid = [c for c in XWalk.columns if bool(re.search("blk", c))][0]
        if keepname == True:
            xwalk_cols = [xwid, to, "".join([to, "name"])]
        else:
            xwalk_cols = [xwid, to]
        lid = [c for c in ["w_geocode", "h_geocode"] if c in self._obj.columns]
        pref = ["".join([c.split("_")[0], "_"]) for c in lid]
        gbid = ["".join([p, c]) for p in pref for c in xwalk_cols[1:]]
        df = self._obj.copy()
        xw = XWalk[xwalk_cols]
        for c, p in zip(lid, pref):
            xwjid = "".join([p, xwid])
            xw = xw.add_prefix(p)
            
            if isinstance(df[c], object):
                df[c] = df[c].astype(np.int64)
            
            if isinstance(xw[xwjid], object):
                xw[xwjid] = xw[xwjid].astype(np.int64)
                
            df = pd.merge(df, xw, left_on=c, right_on=xwjid)
            df = df.drop(columns = [c, xwjid])
        smz_cols = [c for c in df.columns if c not in gbid]
        smz = df.groupby(gbid)[smz_cols].sum().reset_index()
        return smz