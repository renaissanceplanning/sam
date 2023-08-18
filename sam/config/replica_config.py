import datetime

import pandas as pd

replica_regions = {
    "cal_nev": ["06", "32"],
    "great_lakes": ["17", "18", "21", "26", "39", "55"],
    "hawaii": ["15"],
    "mid_atlantic": ["11", "24", "37", "51", "54"],
    "north_atlantic": ["09", "10", "34", "36", "42"],
    "north_central": ["19", "20", "27", "29", "38", "31", "46"],
    "south_atlantic": ["12", "13", "45"],
    "south_central": ["01", "04", "22", "28", "47"],
    "northeast": ["25", "23", "33", "44", "50"],
    "southwest": ["04", "08", "35", "40", "48", "49"],
}

replica_pop_years = ["2019_Q4", 
                     "2021_Q2", "2021_Q4", 
                     "2022_Q2", "2022_Q4"]

replica_coverage_years = pd.Series(
    [int(year[0:4]) for year in replica_pop_years]
    ).unique().tolist()


replica_parcel_years = ["2021_Q4", "2022_Q4"]

age_breaks = [
    -1,
    4,
    9,
    14,
    17,
    19,
    20,
    21,
    24,
    29,
    34,
    39,
    44,
    49,
    55,
    59,
    61,
    64,
    66,
    69,
    74,
    79,
    84,
    1000,
]

age_groups = [
    "age_0_4",
    "age_5_9",
    "age_10_14",
    "age_15_17",
    "age_18_19",
    "age_20",
    "age_21",
    "age_22_24",
    "age_25_29",
    "age_30_34",
    "age_35_39",
    "age_40_44",
    "age_45_49",
    "age_50_54",
    "age_55_59",
    "age_60_61",
    "age_62_64",
    "age_65_66",
    "age_67_69",
    "age_70_74",
    "age_75_79",
    "age_80_84",
    "age_85p",
]

hh_inc_breaks = [
    -1,
    10000,
    15000,
    20000,
    25000,
    30000,
    35000,
    40000,
    45000,
    50000,
    60000,
    75000,
    100000,
    125000,
    150000,
    200000,
    1000000000000,
]

hh_inc_groups = [
    "inc_0_10",
    "inc_10_15",
    "inc_15_20",
    "inc_20_25",
    "inc_25_30",
    "inc_30_35",
    "inc_35_40",
    "inc_40_45",
    "inc_45_50",
    "inc_50_60",
    "inc_60_75",
    "inc_75_100",
    "inc_100_125",
    "inc_125_150",
    "inc_150_200",
    "inc_200p",
]

hh_workers_breaks = [-1, 0, 1, 2, 100]
hh_workers_labels = ["wrk_0", "wrk_1", "wrk_2", "wrk_3p"]

replica_acs_tables = [
    "sex", "age", "hh_income", "hh_vehicles", "tenure", "hh_size", "hh_worker", 
    "education", "race", "ethnicity", "minority_status", "mode_share", "totals"
]
