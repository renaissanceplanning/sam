import os
import pandas as pd

path = os.path.normpath(os.path.abspath(__file__))
path = os.path.abspath(os.path.join(path, "..", "..", "ref_data"))

par_recode = pd.read_csv(os.path.join(path, "land_use_recode.csv"))