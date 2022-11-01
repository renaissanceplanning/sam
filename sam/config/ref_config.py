import os
import pandas as pd
import geopandas as gpd

# pathing to pul in reference data
path = os.path.normpath(os.path.abspath(__file__))
path = os.path.abspath(os.path.join(path, "..", "..", "ref_data"))

par_recode = pd.read_csv(os.path.join(path, "land_use_recode.csv"))
counties = gpd.read_file(os.path.join(path, "counties.geojson"))