# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 14:19:35 2022

@author: Aaron Weinstock
"""

# TODO: aggregates for rent value vehicles
# TODO: change lb to lower_bound
# TODO: Double Check Census Data

import numpy as np
import pandas as pd

census_xw = 'https://www2.census.gov/geo/docs/maps-data/data/rel2020/blkgrp/tab20_blkgrp20_blkgrp10_natl.txt'

xw_2010_to_2020 = pd.read_table(census_xw, delimiter='|')

class ACSConfig:
    """
    Abstract Class to create dataframes formatting ACS columns to human readable
    format.
    """

    def __init__(self, df, table, univ):
        names = np.array(df.columns)
        names = names[names != "lb"]
        # super().__init__(df)
        self._df_ = df
        self._table_ = table
        self._universe_ = univ
        self._names_ = names
        self._reclass_ = "lb" in df.columns


_SEX_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {"B01001_002": "male", "B01001_026": "female"}, orient="index", columns=["full"]
    ),
    table="B01001",
    univ="Total population",
)

_AGE_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B01001_003": ["age_0_4", 0],
            "B01001_004": ["age_5_9", 5],
            "B01001_005": ["age_10_14", 10],
            "B01001_006": ["age_15_17", 15],
            "B01001_007": ["age_18_19", 18],
            "B01001_008": ["age_20", 20],
            "B01001_009": ["age_21", 21],
            "B01001_010": ["age_22_24", 22],
            "B01001_011": ["age_25_29", 25],
            "B01001_012": ["age_30_34", 30],
            "B01001_013": ["age_35_39", 35],
            "B01001_014": ["age_40_44", 40],
            "B01001_015": ["age_45_49", 45],
            "B01001_016": ["age_50_54", 50],
            "B01001_017": ["age_55_59", 55],
            "B01001_018": ["age_60_61", 60],
            "B01001_019": ["age_62_64", 62],
            "B01001_020": ["age_65_66", 65],
            "B01001_021": ["age_67_69", 67],
            "B01001_022": ["age_70_74", 70],
            "B01001_023": ["age_75_79", 75],
            "B01001_024": ["age_80_84", 80],
            "B01001_025": ["age_85p", 85],  # TODO figure out appropriate levels
            "B01001_027": ["age_0_4", 0],
            "B01001_028": ["age_5_9", 5],
            "B01001_029": ["age_10-14", 10],
            "B01001_030": ["age_15_17", 15],
            "B01001_031": ["age_18_19", 18],
            "B01001_032": ["age_20", 20],
            "B01001_033": ["age_21", 21],
            "B01001_034": ["age_22_24", 22],
            "B01001_035": ["age_25_29", 25],
            "B01001_036": ["age_30_34", 30],
            "B01001_037": ["age_35_39", 35],
            "B01001_038": ["age_40_44", 40],
            "B01001_039": ["age_45_49", 45],
            "B01001_040": ["age_50_54", 50],
            "B01001_041": ["age_55_59", 55],
            "B01001_042": ["age_60_61", 60],
            "B01001_043": ["age_62_64", 62],
            "B01001_044": ["age_65_66", 65],
            "B01001_045": ["age_67_69", 67],
            "B01001_046": ["age_70_74", 70],
            "B01001_047": ["age_75_79", 75],
            "B01001_048": ["age_80_84", 80],
            "B01001_049": ["age_85p", 85],  # TODO figure out appropriate levels
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B01001",
    univ="Total population",
)

_AGE_BY_SEX_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B01001_003": ["male_age_0_4", 0],
            "B01001_004": ["male_age_5_9", 5],
            "B01001_005": ["male_age_10-14", 10],
            "B01001_006": ["male_age_15_17", 15],
            "B01001_007": ["male_age_18_19", 18],
            "B01001_008": ["male_age_20", 20],
            "B01001_009": ["male_age_21", 21],
            "B01001_010": ["male_age_22_24", 22],
            "B01001_011": ["male_age_25_29", 25],
            "B01001_012": ["male_age_30_34", 30],
            "B01001_013": ["male_age_35_39", 35],
            "B01001_014": ["male_age_40_44", 40],
            "B01001_015": ["male_age_45_49", 45],
            "B01001_016": ["male_age_50_54", 50],
            "B01001_017": ["male_age_55_59", 55],
            "B01001_018": ["male_age_60_61", 60],
            "B01001_019": ["male_age_62_64", 62],
            "B01001_020": ["male_age_65_66", 65],
            "B01001_021": ["male_age_67_69", 67],
            "B01001_022": ["male_age_70_74", 70],
            "B01001_023": ["male_age_75_79", 75],
            "B01001_024": ["male_age_80_84", 80],
            "B01001_025": ["male_age_85p", 85],  # TODO figure out appropriate levels
            "B01001_027": ["female_age_0_4", 0],
            "B01001_028": ["female_age_5_9", 5],
            "B01001_029": ["female_age_10-14", 10],
            "B01001_030": ["female_age_15_17", 15],
            "B01001_031": ["female_age_18_19", 18],
            "B01001_032": ["female_age_20", 20],
            "B01001_033": ["female_age_21", 21],
            "B01001_034": ["female_age_22_24", 22],
            "B01001_035": ["female_age_25_29", 25],
            "B01001_036": ["female_age_30_34", 30],
            "B01001_037": ["female_age_35_39", 35],
            "B01001_038": ["female_age_40_44", 40],
            "B01001_039": ["female_age_45_49", 45],
            "B01001_040": ["female_age_50_54", 50],
            "B01001_041": ["female_age_55_59", 55],
            "B01001_042": ["female_age_60_61", 60],
            "B01001_043": ["female_age_62_64", 62],
            "B01001_044": ["female_age_65_66", 65],
            "B01001_045": ["female_age_67_69", 67],
            "B01001_046": ["female_age_70_74", 70],
            "B01001_047": ["female_age_75_79", 75],
            "B01001_048": ["female_age_80_84", 80],
            "B01001_049": ["female_age_85p", 85],  # TODO figure out appropriate levels
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B01001",
    univ="Total population",
)

_INCOME_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B19001_002": ["inc_0_10", 0],
            "B19001_003": ["inc_10_15", 10],
            "B19001_004": ["inc_15_20", 15],
            "B19001_005": ["inc_20_25", 20],
            "B19001_006": ["inc_25_30", 25],
            "B19001_007": ["inc_30_35", 30],
            "B19001_008": ["inc_35_40", 35],
            "B19001_009": ["inc_40_45", 40],
            "B19001_010": ["inc_45_50", 45],
            "B19001_011": ["inc_50_60", 50],
            "B19001_012": ["inc_60_75", 60],
            "B19001_013": ["inc_75_100", 75],
            "B19001_014": ["inc_100_125", 100],
            "B19001_015": ["inc_125_150", 125],
            "B19001_016": ["inc_150_200", 150],
            "B19001_017": ["inc_200p", 200],  # TODO figure out appropriate levels
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B19001",
    univ="Total households",
)

_RIP_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "C17002_002": ["rip_0_05", 0],
            "C17002_003": ["rip_05_1", 0.5],
            "C17002_004": ["rip_1_125", 1],
            "C17002_005": ["rip_125_15", 1.25],
            "C17002_006": ["rip_15_185", 1.5],
            "C17002_007": ["rip_185_2", 1.85],
            "C17002_008": ["rip_2p", 2],  # TODO figure out appropriate levels
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="C17002",
    univ="Population for whom poverty status is determined",
)

_VEHICLES_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B25044_003": ["veh_0", 0],
            "B25044_004": ["veh_1", 1],
            "B25044_005": ["veh_2", 2],
            "B25044_006": ["veh_3", 3],
            "B25044_007": ["veh_4", 4],
            "B25044_008": ["veh_5p", 5],  # TODO figure out appropriate levels
            "B25044_010": ["veh_0", 0],
            "B25044_011": ["veh_1", 1],
            "B25044_012": ["veh_2", 2],
            "B25044_013": ["veh_3", 3],
            "B25044_014": ["veh_4", 4],
            "B25044_015": ["veh_5p", 5],  # TODO figure out appropriate levels
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B25044",
    univ="Total households",
)

_TENURE_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {"B25044_002": "own", "B25044_009": "rent"}, 
        orient="index", columns=["full"]
    ),
    table="B25044",
    univ="Total households",
)

_YEAR_MOVED_IN_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B25038_001": ["tot_mvd", "tot_mvd", "tot_mvd", "tot_mvd",
                           "tot_mvd", "tot_mvd", "tot_mvd"],
            "B25038_003": ["rnt_2021p", "rnt_2021p",
                           "rnt_2019p", "rnt_2019p", "rnt_2017p", "rnt_2017p", 
                           "rnt_2015p", "rnt_2015p", "rnt_2015p"],
            "B25038_004": ["rnt_2018_2020", "rnt_2018_2020", 
                           "rnt_2015_2018", "rnt_2015_2018", "rnt_2015_2016", 
                           "rnt_2015_2016", "rnt_2010_2014", "rnt_2010_2014", 
                           "rnt_2010_2014"],
            "B25038_005": ["rnt_2010_2017", "rnt_2010_2017", 
                           "rnt_2010_2014", "rnt_2010_2014", "rnt_2010_2014", 
                           "rnt_2010_2014", "rnt_2000_2009", "rnt_2000_2009", 
                           "rnt_2000_2009"],
            "B25038_006": ["rnt_2000_2009", "rnt_2000_2009",
                           "rnt_2000_2009", "rnt_2000_2009", "rnt_2000_2009",
                           "rnt_2000_2009", "rnt_1990_1999", "rnt_1990_1999", 
                           "rnt_1990_1999"],
            "B25038_007": ["rnt_1990_1999", "rnt_1990_1999", 
                           "rnt_1990_1999", "rnt_1990_1999", "rnt_1990_1999", 
                           "rnt_1990_1999", "rnt_1980_1989", "rnt_1980_1989", 
                           "rnt_1980_1989"],
            "B25038_008": ["rnt_1989b", "rnt_1989b", 
                           "rnt_1989b", "rnt_1989b", "rnt_1989b", 
                           "rnt_1989b", "rnt_1979b", "rnt_1979b",
                           "rnt_1979b"],
            "B25038_010": ["own_2021p", "own_2021p",
                           "own_2019p", "own_2019p", "own_2017p", "own_2017p", 
                           "own_2015p", "own_2015p", "own_2015p"],
            "B25038_011": ["own_2018_2020", "own_2018_2020", 
                           "own_2015_2018", "own_2015_2018", "own_2015_2016", 
                           "own_2015_2016", "own_2010_2014", "own_2010_2014", 
                           "own_2010_2014"],
            "B25038_012": ["own_2010_2017", "own_2010_2017", 
                           "own_2010_2014", "own_2010_2014", "own_2010_2014", 
                           "own_2010_2014", "own_2000_2009", "own_2000_2009", 
                           "own_2000_2009"],
            "B25038_013": ["own_2000_2009", "own_2000_2009", 
                           "own_2000_2009", "own_2000_2009", "own_2000_2009", 
                           "own_2000_2009", "own_1990_1999", "own_1990_1999", 
                           "own_1990_1999"],
            "B25038_014": ["own_1990_1999", "own_1990_1999", 
                           "own_1990_1999", "own_1990_1999", "own_1990_1999", 
                           "own_1990_1999", "own_1980_1989", "own_1980_1989", 
                           "own_1980_1989"],
            "B25038_015": ["own_1989b", "own_1989b", 
                           "own_1989b", "own_1989b", "own_1989b", "own_1989b", 
                           "own_1979b", "own_1979b", "own_1979b"],

        },
        orient="index",
        columns=['2023', "2022", "2021", '2020', '2019', '2018', '2017', '2016', '2015'],
    ),
    table="B25038",
    univ="Total Population in Occupied Housing Units",
)

_YEAR_BLT__ = ACSConfig( #TODO flip so new years area added to the end
     pd.DataFrame.from_dict(
        {
            "B25034_001": ["tot_blt", "tot_blt", "tot_blt", "tot_blt", 
                           "tot_blt", "tot_blt", "tot_blt", "tot_blt"],
            "B25034_002":['blt_2020p', 'blt_2020p', 'blt_2020p', 'blt_2014p', 'blt_2014p', 
                          'blt_2014p', 'blt_2014p', 'blt_2014p', 'blt_2014p'],
            "B25034_003":[
                'blt_2010_2019', 'blt_2010_2019',  
                'blt_2010_2019', 'blt_2010_2013', 'blt_2010_2013', 
                'blt_2010_2013', 'blt_2010_2013', 'blt_2010_2013', 
                'blt_2010_2013'],
            "B25034_004":[
                'blt_2000_2009', 'blt_2000_2009', 
                'blt_2000_2009', 'blt_2000_2009', 'blt_2000_2009', 
                'blt_2000_2009', 'blt_2000_2009', 'blt_2000_2009', 
                'blt_2000_2009'],
            "B25034_005":[
                'blt_1990_1999', 'blt_1990_1999',
                'blt_1990_1999', 'blt_1990_1999', 'blt_1990_1999', 
                'blt_1990_1999', 'blt_1990_1999', 'blt_1990_1999', 
                'blt_1990_1999'],
            "B25034_006":[
                'blt_1980_1989', 'blt_1980_1989',
                'blt_1980_1989', 'blt_1980_1989', 'blt_1980_1989', 
                'blt_1980_1989', 'blt_1980_1989', 'blt_1980_1989', 
                'blt_1980_1989'],
            "B25034_007":[
                'blt_1970_1979', 'blt_1970_1979',
                'blt_1970_1979', 'blt_1970_1979', 'blt_1970_1979', 
                'blt_1970_1979', 'blt_1970_1979', 'blt_1970_1979', 
                'blt_1970_1979'],
            "B25034_008":[
                'blt_1960_1969', 'blt_1960_1969',
                'blt_1960_1969', 'blt_1960_1969', 'blt_1960_1969', 
                'blt_1960_1969', 'blt_1960_1969', 'blt_1960_1969', 
                'blt_1960_1969'],
            "B25034_009":[
                'blt_1950_1960', 'blt_1950_1960', 
                'blt_1950_1960', 'blt_1950_1960', 'blt_1950_1960', 
                'blt_1950_1960', 'blt_1950_1960', 'blt_1950_1960', 
                'blt_1950_1960'],
            "B25034_010":[
                'blt_1940_1949', 'blt_1940_1949',
                'blt_1940_1949', 'blt_1940_1949', 'blt_1940_1949', 
                'blt_1940_1949', 'blt_1940_1949', 'blt_1940_1949', 
                'blt_1940_1949'],
            "B25034_011":[
                'blt_1939b', 'blt_1939b', 
                'blt_1939b', 'blt_1939b', 'blt_1939b', 'blt_1939b', 
                'blt_1939b', 'blt_1939b', 'blt_1939b'],
        },
        orient="index",
        columns=['2023', '2022', "2021", '2020', '2019', '2018', '2017', '2016', '2015'],
    ),
    table="B25034",
    univ="Total Population in Occupied Housing Units",    
)

_DISABILITY_BG_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "C21007_005": "yes",
            "C21007_008": "yes",
            "C21007_012": "yes",
            "C21007_015": "yes",
            "C21007_020": "yes",
            "C21007_023": "yes",
            "C21007_027": "yes",
            "C21007_030": "yes",
            "C21007_006": "no",
            "C21007_009": "no",
            "C21007_013": "no",
            "C21007_016": "no",
            "C21007_021": "no",
            "C21007_024": "no",
            "C21007_028": "no",
            "C21007_031": "no",
        },
        orient="index",
        columns=["full"],
    ),
    table="C21007",
    univ="Civilian 18+ population for whom poverty status can be determined",
)

_DISABILITY_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B18101_004": "yes",
            "B18101_007": "yes",
            "B18101_010": "yes",
            "B18101_013": "yes",
            "B18101_016": "yes",
            "B18101_019": "yes",
            "B18101_023": "yes",
            "B18101_026": "yes",
            "B18101_029": "yes",
            "B18101_032": "yes",
            "B18101_035": "yes",
            "B18101_038": "yes",
            "B18101_005": "no",
            "B18101_008": "no",
            "B18101_011": "no",
            "B18101_014": "no",
            "B18101_017": "no",
            "B18101_020": "no",
            "B18101_024": "no",
            "B18101_027": "no",
            "B18101_030": "no",
            "B18101_033": "no",
            "B18101_036": "no",
            "B18101_039": "no",
        },
        orient="index",
        columns=["full"],
    ),
    table="B18101",
    univ="Civilian non-institutionalized population",
)

_SIZE_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B25009_003": ["size_1", 1],
            "B25009_004": ["size_2", 2],
            "B25009_005": ["size_3", 3],
            "B25009_006": ["size_4", 4],
            "B25009_007": ["size_5", 5],
            "B25009_008": ["size_6", 6],
            "B25009_009": ["size_7p", 7],
            "B25009_011": ["size_1", 1],
            "B25009_012": ["size_2", 2],
            "B25009_013": ["size_3", 3],
            "B25009_014": ["size_4", 4],
            "B25009_015": ["size_5", 5],
            "B25009_016": ["size_6", 6],
            "B25009_017": ["size_7p", 7],
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B25009",
    univ="Total households",
)

_WORKERS_BG_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B23009_004": ["wrk_0", 0],
            "B23009_014": ["wrk_0", 0],
            "B23009_019": ["wrk_0", 0],
            "B23009_025": ["wrk_0", 0],
            "B23009_035": ["wrk_0", 0],
            "B23009_040": ["wrk_0", 0],
            "B23009_005": ["wrk_1", 1],
            "B23009_015": ["wrk_1", 1],
            "B23009_020": ["wrk_1", 1],
            "B23009_026": ["wrk_1", 1],
            "B23009_036": ["wrk_1", 1],
            "B23009_041": ["wrk_1", 1],
            "B23009_006": ["wrk_2", 2],
            "B23009_016": ["wrk_2", 2],
            "B23009_021": ["wrk_2", 2],
            "B23009_027": ["wrk_2", 2],
            "B23009_037": ["wrk_2", 2],
            "B23009_042": ["wrk_2", 2],
            "B23009_009": ["wrk_3p", 3],
            "B23009_017": ["wrk_3p", 3],
            "B23009_022": ["wrk_3p", 3],
            "B23009_030": ["wrk_3p", 3],
            "B23009_038": ["wrk_3p", 3],
            "B23009_043": ["wrk_3p", 3],
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B23009",
    univ="Family households",
)

_WORKERS_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B08203_007": ["wrk_0", 0],
            "B08203_013": ["wrk_1", 1],
            "B08203_019": ["wrk_2", 2],
            "B08203_025": ["wrk_3p", 3],  # TODO figure out appropriate levels
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B08203",
    univ="Total households",
)

_EDUCATION_BG_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B29002_002": ["lths", "lths"],
            "B29002_003": ["shs", "lths"],
            "B29002_004": ["hs", "hs"],
            "B29002_005": ["scnd", "scndassc"],
            "B29002_006": ["assc", "scndassc"],
            "B29002_007": ["bach", "bach"],
            "B29002_008": ["gradprof", "gradprof"],
        },
        orient="index",
        columns=["full", "basic"],
    ),
    table="B29002",
    univ="25+ population",
)

_EDUCATION_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B15001_004": ["lths", "lths"],
            "B15001_012": ["lths", "lths"],
            "B15001_020": ["lths", "lths"],
            "B15001_028": ["lths", "lths"],
            "B15001_036": ["lths", "lths"],
            "B15001_045": ["lths", "lths"],
            "B15001_053": ["lths", "lths"],
            "B15001_061": ["lths", "lths"],
            "B15001_069": ["lths", "lths"],
            "B15001_077": ["lths", "lths"],
            "B15001_005": ["shs", "lths"],
            "B15001_013": ["shs", "lths"],
            "B15001_021": ["shs", "lths"],
            "B15001_029": ["shs", "lths"],
            "B15001_037": ["shs", "lths"],
            "B15001_046": ["shs", "lths"],
            "B15001_054": ["shs", "lths"],
            "B15001_062": ["shs", "lths"],
            "B15001_070": ["shs", "lths"],
            "B15001_078": ["shs", "lths"],
            "B15001_006": ["hs", "hs"],
            "B15001_014": ["hs", "hs"],
            "B15001_022": ["hs", "hs"],
            "B15001_030": ["hs", "hs"],
            "B15001_038": ["hs", "hs"],
            "B15001_047": ["hs", "hs"],
            "B15001_055": ["hs", "hs"],
            "B15001_063": ["hs", "hs"],
            "B15001_071": ["hs", "hs"],
            "B15001_079": ["hs", "hs"],
            "B15001_007": ["scnd", "scndassc"],
            "B15001_015": ["scnd", "scndassc"],
            "B15001_023": ["scnd", "scndassc"],
            "B15001_031": ["scnd", "scndassc"],
            "B15001_039": ["scnd", "scndassc"],
            "B15001_048": ["scnd", "scndassc"],
            "B15001_056": ["scnd", "scndassc"],
            "B15001_064": ["scnd", "scndassc"],
            "B15001_072": ["scnd", "scndassc"],
            "B15001_080": ["scnd", "scndassc"],
            "B15001_008": ["assc", "scndassc"],
            "B15001_016": ["assc", "scndassc"],
            "B15001_024": ["assc", "scndassc"],
            "B15001_032": ["assc", "scndassc"],
            "B15001_040": ["assc", "scndassc"],
            "B15001_049": ["assc", "scndassc"],
            "B15001_057": ["assc", "scndassc"],
            "B15001_065": ["assc", "scndassc"],
            "B15001_073": ["assc", "scndassc"],
            "B15001_081": ["assc", "scndassc"],
            "B15001_009": ["bach", "bach"],
            "B15001_017": ["bach", "bach"],
            "B15001_025": ["bach", "bach"],
            "B15001_033": ["bach", "bach"],
            "B15001_041": ["bach", "bach"],
            "B15001_050": ["bach", "bach"],
            "B15001_058": ["bach", "bach"],
            "B15001_066": ["bach", "bach"],
            "B15001_074": ["bach", "bach"],
            "B15001_082": ["bach", "bach"],
            "B15001_010": ["gradprof", "gradprof"],
            "B15001_018": ["gradprof", "gradprof"],
            "B15001_026": ["gradprof", "gradprof"],
            "B15001_034": ["gradprof", "gradprof"],
            "B15001_042": ["gradprof", "gradprof"],
            "B15001_051": ["gradprof", "gradprof"],
            "B15001_059": ["gradprof", "gradprof"],
            "B15001_067": ["gradprof", "gradprof"],
            "B15001_075": ["gradprof", "gradprof"],
            "B15001_083": ["gradprof", "gradprof"],
        },
        orient="index",
        columns=["full", "basic"],
    ),
    table="B15001",
    univ="18+ population",
)

_MIGRATION_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B07001_017": "same_house",
            "B07001_033": "same_county",
            "B07001_049": "same_state",
            "B07001_065": "diff_state",
            "B07001_081": "diff_country",
        },
        orient="index",
        columns=["full"],
    ),
    table="B07001",
    univ="1+ population",
)

_RACE_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B02001_002": "white",
            "B02001_003": "black",
            "B02001_004": "aian",
            "B02001_005": "asian",
            "B02001_006": "nhopi",
            "B02001_007": "other_race",
            "B02001_008": "twoplus",
        },
        orient="index",
        columns=["full"],
    ),
    table="B02001",
    univ="Total population",
)

_ETHNICITY_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B03002_002": "nonhisp",
            "B03002_012": "hisp",
        },
        orient="index",
        columns=["full"],
    ),
    table="B03002",
    univ="Total population",
)

_MINORITY_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B03002_003": "nonmnty",
            "B03002_004": "mnty",
            "B03002_005": "mnty",
            "B03002_006": "mnty",
            "B03002_007": "mnty",
            "B03002_008": "mnty",
            "B03002_009": "mnty",
            "B03002_013": "mnty",
            "B03002_014": "mnty",
            "B03002_015": "mnty",
            "B03002_016": "mnty",
            "B03002_017": "mnty",
            "B03002_018": "mnty",
            "B03002_019": "mnty",
        },
        orient="index",
        columns=["full"],
    ),
    table="B03002",
    univ="Total population",
)

_MODE_SHARE_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B08301_001": ["trips", "trips"],
            "B08301_002": ["car", "auto"],
            "B08301_003": ["car_1", ""],
            "B08301_004": ["car_2p", ""],
            "B08301_005": ["car_2p_2", ""],
            "B08301_006": ["car_2p_3", ""],
            "B08301_007": ["car_2p_4", ""],
            "B08301_008": ["car_2p_56", ""],
            "B08301_009": ["car_2p_7p", ""],
            "B08301_010": ["tran", "transit"],
            "B08301_011": ["tran_bus", ""],
            "B08301_012": ["tran_ser", ""],
            "B08301_013": ["tran_ldtcr", ""],
            "B08301_014": ["tran_lrst", ""],
            "B08301_015": ["tran_ferry", ""],
            "B08301_016": ["taxi", "other_mode"],
            "B08301_017": ["motorcycle", "auto"],
            "B08301_018": ["bike", "nonmot"],
            "B08301_019": ["walk", "nonmot"],
            "B08301_020": ["other_mode", "other_mode"],
            "B08301_021": ["wfh", "wfh"],
        },
        orient="index",
        columns=["full", "basic"],
    ),
    table="B08301",
    univ="16+ working population",
)

_TOT_POP_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict({"B01003_001": "pop"}, orient="index", columns=["full"]),
    table="B01003",
    univ="Total population",
)

_TOT_HH_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict({"B11012_001": "hh"}, orient="index", columns=["full"]),
    table="B11012",
    univ="Total households",
)

_TOT_HU_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict({"B25001_001": "hu"}, orient="index", columns=["full"]),
    table="B25001",
    univ="Total housing units",
)

_RENT_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B25056_003": ["rnt_1_100", 1],
            "B25056_004": ["rnt_100_149", 100],
            "B25056_005": ["rnt_150_199", 150],
            "B25056_006": ["rnt_200_249", 200],
            "B25056_007": ["rnt_250_299", 250],
            "B25056_008": ["rnt_300_349", 300],
            "B25056_009": ["rnt_350_399", 350],
            "B25056_010": ["rnt_400_449", 400],
            "B25056_011": ["rnt_450_499", 450],
            "B25056_012": ["rnt_500_549", 500],
            "B25056_013": ["rnt_550_599", 550],
            "B25056_014": ["rnt_600_649", 600],
            "B25056_015": ["rnt_650_699", 650],
            "B25056_016": ["rnt_700_749", 700],
            "B25056_017": ["rnt_750_799", 750],
            "B25056_018": ["rnt_800_899", 800],
            "B25056_019": ["rnt_900_999", 900],
            "B25056_020": ["rnt_1000_1249", 1000],
            "B25056_021": ["rnt_1250_1499", 1250],
            "B25056_022": ["rnt_1500_1999", 1500],
            "B25056_023": ["rnt_2000_2499", 2000],
            "B25056_024": ["rnt_2500_2999", 2500],
            "B25056_025": ["rnt_3000_3499", 3000],
            "B25056_026": ["rnt_3500p", 3500],
            "B25056_027": ["rnt_none", 0],
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B25056",
    univ="Renter-occupied housing units",
)

_VALUE_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            "B25075_002": ["hval_10000", 0],
            "B25075_003": ["hval_10000_14999", 10000],
            "B25075_004": ["hval_15000_19999", 15000],
            "B25075_005": ["hval_20000_24999", 20000],
            "B25075_006": ["hval_25000_29999", 25000],
            "B25075_007": ["hval_30000_34999", 30000],
            "B25075_008": ["hval_35000_39999", 35000],
            "B25075_009": ["hval_40000_49999", 40000],
            "B25075_010": ["hval_50000_59999", 50000],
            "B25075_011": ["hval_60000_69999", 60000],
            "B25075_012": ["hval_70000_79999", 70000],
            "B25075_013": ["hval_80000_89999", 80000],
            "B25075_014": ["hval_90000_99999", 90000],
            "B25075_015": ["hval_100000_124999", 100000],
            "B25075_016": ["hval_125000_149999", 125000],
            "B25075_017": ["hval_150000_174999", 150000],
            "B25075_018": ["hval_175000_199999", 175000],
            "B25075_019": ["hval_200000_249999", 200000],
            "B25075_020": ["hval_250000_299999", 250000],
            "B25075_021": ["hval_300000_399999", 300000],
            "B25075_022": ["hval_400000_499999", 400000],
            "B25075_023": ["hval_500000_749999", 500000],
            "B25075_024": ["hval_750000_999999", 750000],
            "B25075_025": ["hval_1000000_1499999", 1000000],
            "B25075_026": ["hval_1500000_1999999", 1500000],
            "B25075_027": ["hval_2000000p", 2000000],
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B25075",
    univ="Owner-occupied Housing Units",
)

_COST_CONFIG_ = ACSConfig(
    pd.DataFrame.from_dict(
        {
            # Morgages
            "B25087_003": ["hm_costs_200", 0],
            "B25087_004": ["hm_costs_200_299", 200],
            "B25087_005": ["hm_costs_300_399", 300],
            "B25087_006": ["hm_costs_400_499", 400],
            "B25087_007": ["hm_costs_500_599", 500],
            "B25087_008": ["hm_costs_600_699", 600],
            "B25087_009": ["hm_costs_700_799", 700],
            "B25087_010": ["hm_costs_800_899", 800],
            "B25087_011": ["hm_costs_900_999", 900],
            "B25087_012": ["hm_costs_1,000_1,249", 1000],
            "B25087_013": ["hm_costs_1,250_1,499", 1250],
            "B25087_014": ["hm_costs_1,500_1,999", 1500],
            "B25087_015": ["hm_costs_2,000_2,499", 2000],
            "B25087_016": ["hm_costs_2,500_2,999", 2500],
            "B25087_017": ["hm_costs_3,000p", 3000],
            # no mortgage
            "B25087_019": ["hn_costs_100", 0],
            "B25087_020": ["hn_costs_100_149", 100],
            "B25087_021": ["hn_costs_150_199", 150],
            "B25087_022": ["hn_costs_200_249", 200],
            "B25087_023": ["hn_costs_250_299", 250],
            "B25087_024": ["hn_costs_300_349", 300],
            "B25087_025": ["hn_costs_350_399", 350],
            "B25087_026": ["hn_costs_400_499", 400],
            "B25087_027": ["hn_costs_500_599", 500],
            "B25087_028": ["hn_costs_600_699", 600],
            "B25087_029": ["hn_costs_700p", 700],
        },
        orient="index",
        columns=["full", "lb"],
    ),
    table="B25087",
    univ="Owner-occupied Housing Units",
)
