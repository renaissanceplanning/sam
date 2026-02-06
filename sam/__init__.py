# import pydata_google_auth

# Initialize logging (must be before other imports)
from .logging_config import setup_logging, get_logger
setup_logging()

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

from .menus import DataMenuDownloader

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