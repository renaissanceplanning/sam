import os
import sys

from rpy2 import situation

r_home = situation.r_home_from_registry()
if r_home is None:
    r_home = os.path.join(sys.exec_prefix, "lib", "R")
os.environ["R_HOME"] = r_home

from . import config
from . import acs
from . import download
from . import lihtc
from . import lodes
from . import menus
from . import osm
from . import parcels
from . import tiger
from . import replica


