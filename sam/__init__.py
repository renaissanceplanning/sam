import os
import sys
# import pydata_google_auth

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

from .menus import dataMenuDownloader

# """ 
#     integrated into the init of replica module and will only run the first time sam is imported 
#     for a user of the codebase. 
#     Credentials are stored here typically:
#         $APPDATA/Roaming/pydata/pydate_google_credentials.json
# """

# SCOPES = [
#     "https://www.googleapis.com/auth/cloud-platform",
# ]

# CRED = pydata_google_auth.get_user_credentials(SCOPES)