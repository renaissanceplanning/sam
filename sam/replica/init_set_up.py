import pandas_gbq 
import pydata_google_auth 

if __name__ == "__main__":
    SCOPES = [ 
        'https://www.googleapis.com/auth/cloud-platform', 
        'https://www.googleapis.com/auth/drive', 
    ]

    credentials = pydata_google_auth.get_user_credentials(SCOPES)