# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 15:42:42 2022

@author: Aaron Weinstock
"""

import re
import numpy as np
import pandas as pd

from rputils.download.census import dl_lodes, dl_xwalk

# %% Helper functions


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
    df = dl_lodes(file=file, ST=state, TYPE="JT00", YEAR=year, SEG="S000", PART=None)
    df[idcol] = df[idcol].astype(str)
    df = df.drop(columns="createdate")
    return df


# %% Class


class XWalk(pd.DataFrame):
    """
    Download a state's geography crosswalk.
    """

    def __init__(self, df, ST):
        super().__init__(df)
        self.__datastate__ = ST

    @classmethod
    def xwalk(cls, state):
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
        return cls(df, state)

    def to_csv(self, save_path):
        """
        Save crosswalk data as a .csv.

        Parameters
        ----------
        save_path : str
            Path to which to save the .csv.

        Returns
        -------
        None.

        """
        self.to_csv(save_path, index=False)


class LODES(pd.DataFrame):
    """
    Download LODES data
    """

    def __init__(self, df, ST):
        super().__init__(df)
        self.__datastate__ = ST

    @classmethod
    def rac(cls, state, year):
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
        return cls(df=df, ST=state)

    @classmethod
    def wac(cls, state, year):
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
        return cls(df=df, ST=state)

    @classmethod
    def od(cls, state, year):
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
        return cls(df=df, ST=state)



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
        if self.__datastate__ == XWalk.__datastate__:
            pass
        else:
            raise ValueError(
                "LODES state != XWalk state; "
                f"{self.__datastate__} and {XWalk.__datastate__}"
            )
        agg_opts = [
            c
            for c in XWalk.columns
            if np.logical_and(
                bool(re.search("blk", c)) == False, bool(re.search("name$", c)) == False
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
        lid = [c for c in ["w_geocode", "h_geocode"] if c in self.columns]
        pref = ["".join([c.split("_")[0], "_"]) for c in lid]
        gbid = ["".join([p, c]) for p in pref for c in xwalk_cols[1:]]
        df = self.copy()
        xw = XWalk[xwalk_cols]
        for c, p in zip(lid, pref):
            xwjid = "".join([p, xwid])
            df = pd.merge(df, xw.add_prefix(p), left_on=c, right_on=xwjid)
            df = df.drop(xwjid)
        smz_cols = [c for c in df.columns if c not in gbid]
        smz = df.groupby(gbid)[smz_cols].sum().reset_index()
        return smz

    def to_csv(self, save_path):
        """
        Save LODES data as a .csv.

        Parameters
        ----------
        save_path : str
            Path to which to save the .csv.

        Returns
        -------
        None.

        """
        self.to_csv(save_path, index=False)
