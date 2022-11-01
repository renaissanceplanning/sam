"""
Basic methods supporting downloads
"""

# %% IMPORTS
import os
import re
from urllib import request
import requests
from requests.exceptions import RequestException
from rputils.core import make_path


# %% FUNCTIONS
def download_file_from_url(url, save_path):
    """
    Downloads file resources directly from a url endpoint to a folder.

    Args:
        url (str): String; path to resource
        save_path (str): String; path to output file

    Returns:
        None
    """
    if os.path.isdir(save_path):
        filename = get_filename_from_header(url)
        save_path = make_path(save_path, filename)

    print(f"...downloading {save_path} from {url}")
    try:
        request.urlretrieve(url, save_path)
    except:
        with request.urlopen(url) as download:
            with open(save_path, "wb") as out_file:
                out_file.write(download.read())


def get_filename_from_header(url):
    """
    Grabs a filename provided in the url object header.

    Args:
        url (str): string, url path to file on server

    Returns:
        filename (str): filename as string
    """
    try:
        with requests.get(url) as r:
            if "Content-Disposition" in r.headers.keys():
                return re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]
            else:
                return url.split("/")[-1]
    except RequestException as e:
        print(e)
