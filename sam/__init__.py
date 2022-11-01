import os
import sys
from rpy2 import situation

r_home = situation.r_home_from_registry()
if r_home is None:
    r_home = os.path.join(sys.exec_prefix, "lib", "R")
os.environ["R_HOME"] = r_home

#os.environ['R_HOME'] = r"C:\Program Files\R\R-4.0.2"

from . import acs
from . import config
from . import download
from . import lihtc
from . import lodes
from . import menus
from . import osm
from . import parcels
from . import tiger

