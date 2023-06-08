import pydata_google_auth

""" 
    initially used as a mechanism to get credentials for REPLICA data, not integrated into the init of
    replica module and will only run the first time sam is imported for a user of the codebase. 
    Credentials are stored here typically:
        $APPDATA/Roaming/pydata/pydate_google_credentials.json
"""

if __name__ == "__main__":
    SCOPES = [
        "https://www.googleapis.com/auth/cloud-platform",
    ]

    credentials = pydata_google_auth.get_user_credentials(SCOPES)
