# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 14:21:22 2022

@author: AZ7
"""

import pandas as pd
import numpy as np

class ACS(pd.DataFrame):
    def __init__(self, df, univ):
        super().__init__(df)
        self.__universe__ = univ
        
    def _combine_levels(df, idcol, config, bounds=None, name=None):
        if bounds is not None and name is None:
            dt = df.pivot(index=idcol,
                          columns="variable",
                          values="estimate")
            dt = dt.reset_index().drop(columns="variable")
            pref = df.alias.iloc[0].split("_")[0]
            bounds = [0] + np.sort(bounds).tolist()  + [np.inf]
            cols = [idcol]
            for i in np.arange(len(bounds)-1):
                l = bounds[i]
                u = bounds[i+1]
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
        elif bounds is None and name is not None:
            cfg = config.reset_index().rename(columns={"index":"variable"})
            cfg = cfg[["variable",name]]
            dt = df.merge(cfg, on="variable", how="inner")
            dt = dt.groupby([idcol,name])[["estimate"]].sum().reset_index()
            dt = dt.pivot_wider(index=idcol, columns=name, value="estimate")
            dt = dt.reset_index().drop(columns=name)
        else:
            raise ValueError("One of bounds and name must be provided, and "\
                             "the other must be None")
        return dt
    
    def to_csv(self, save_path):
        self.to_csv(save_path)
        
            
                
                
        