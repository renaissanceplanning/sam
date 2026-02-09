# general configuration imports
from .ref_config import PAR_RECODE, COUNTIES, STATE_DF, TEST_AOI, FL_TO_REPLICA, CENSUS_XW
from .helper_functions import is_int, validate_data_dir, extract_fips
from .parcel_config import fl_par_config_csv as PAR_CONF

# module config imports
from . import acs_config as ACS_CONF
from . import ref_config as REF_CONF
from .replica_config import replica_regions
from .menus import *

CENSUS_API_KEY = "069cfb8bf769673e697705dc52eb849c4d9b47b5"


def ensure_censusdis_api_key():
    """
    Ensure censusdis can find Census API key.

    censusdis looks for API key in ~/.censusdis/api_key.txt
    This function creates that file if it doesn't exist.
    """
    from pathlib import Path
    import logging

    logger = logging.getLogger(__name__)

    api_key_file = Path.home() / '.censusdis' / 'api_key.txt'

    if not api_key_file.exists():
        api_key_file.parent.mkdir(exist_ok=True)
        api_key_file.write_text(CENSUS_API_KEY)
        logger.info(f"Created censusdis API key file: {api_key_file}")


# Set up censusdis API key on import
ensure_censusdis_api_key()

# Optional Google Cloud authentication - only needed for Replica data
try:
    import pydata_google_auth

    """
        integrated into the init of replica module and will only run the first time sam is imported
        for a user of the codebase.
        Credentials are stored here typically:
            $APPDATA/Roaming/pydata/pydate_google_credentials.json
    """

    SCOPES = [
        "https://www.googleapis.com/auth/cloud-platform",
    ]

    CRED = pydata_google_auth.get_user_credentials(SCOPES)
except ImportError:
    # Google Cloud authentication not available
    # Replica data functionality will not work without this
    CRED = None