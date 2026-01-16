"""
Replica data module.

Provides access to Replica synthetic population, network, and trip data.
Requires Google Cloud authentication for API access.

#     integrated into the init of replica module and will only run the first time sam is imported 
#     for a user of the codebase. 
#     Credentials are stored here typically:
#         $APPDATA/Roaming/pydata/pydate_google_credentials.json
#
# SCOPES = [
#     "https://www.googleapis.com/auth/cloud-platform",
# ]
#
# CRED = pydata_google_auth.get_user_credentials(SCOPES)
"""

from .core import Replica

__all__ = ['Replica']
