# -*- coding: utf-8 -*-
"""
Created on Thu Sep 23 16:17:50 2021

@author: AZ7
"""

# %% Imports

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re 
from urllib.parse import urlparse
import pandas as pd
from zipfile import ZipFile
from io import BytesIO
import numpy as np
import fiona
import geopandas as gpd



# %% Functions

def pad_links_by_state():
    '''
    Produce a table of all PAD shapefiles available at the state level by
    scraping the USGS site for protected areas. PAD state shapefiles are stored
    in zip archives for the state; this function will identify the link to
    the zip archive for each state, as well as list all PAD files available
    in the archive.

    Notes
    -----
    The different types of PAD files are defined as follows:
        - Fee: open space lands owned outright by public Federal, State, and
        local agencies, nonprofits, or privately owned lands
        - Easement: conservation and open space easements provided as is by
        the National Conservation Easement Database (NCED), including those on
        private as well as public lands (some easements are not provided to
        PAD-US due to NCED procedures on confidentiality).
        - Designation: boundaries of policy-designated areas, such as
        Wilderness, Wild & Scenic Rivers, National Monuments and others –
        these boundaries sometimes do not align with fee ownerships, due to
        their delineation in laws or regulations.
        - Proclamation: boundaries of the administrative area of National
        Forests, Parks, Wildlife Refuges and other lands. These are not
        ownership lines but are used for agency administration purposes. Some
        proclamation boundaries can cover extremely large areas of private
        land, while others are close to ownership boundaries. In any case,
        it’s important not to consider proclamation boundaries as reflecting
        actual land ownership – they’re just for agency administration
        purposes.
        - Marine: boundaries of Marine Protected Areas (MPAs) and reserves
        managed by NOAA as well as equivalent designations for areas managed by
        States; this layer also includes vast Outer Continental Shelf areas
        managed by the Bureau of Ocean Energy Management (BOEM).
    Note that the areas covered by these unique files can (and often do)
    overlap. For more details, see:
    http://www.protectedlands.net/pad-us-technical-how-tos/

    Returns
    -------
    pandas.DataFrame
        A four column table detailing access to PAD state shapefiles:
            - state_USPS: 2-character state USPS code
            - PAD_type: type of PAD file (e.g. Designation, Fee, etc.)
            - PAD_file: name of the file within the zip archive for the state
            - PAD_link: url to the zip archive for the state
        The "state_USPS" and "PAD_type" columns can be used to filter the
        data; the "PAD_file" and "PAD_link" columns can be passed as inputs
        to `read_pad` to load files of interest.

    '''
    # Find the PAD-US data page on the home site
    home_link = "https://www.usgs.gov/core-science-systems/science-analytics-and-synthesis/gap/science/protected-areas"
    home_req = Request(home_link)
    home_page = urlopen(home_req)
    home_soup = BeautifulSoup(home_page, "lxml")
    for link in home_soup.findAll('a'):
        if link.string is None:
            pass
        else:
            if bool(re.search("data download", link.string, re.IGNORECASE)) == True:
                data_link = link.get("href")
                break
            else:
                pass
    if bool(re.search("^/", data_link)) == True:
        home_parsed = urlparse(home_link)
        home_base = '://'.join([home_parsed.scheme, home_parsed.netloc])
        data_link = ''.join([home_base, data_link])
    else:
        pass
    # Find the download page on the data page
    data_req = Request(data_link)
    data_page = urlopen(data_req)
    data_soup = BeautifulSoup(data_page, "lxml")
    for link in data_soup.findAll('a'):
        if link.string is None:
            pass
        else:
            if bool(re.search("data download", link.string, re.IGNORECASE)) == True:
                dl_link = link.get("href")
                break
            else:
                pass
    if bool(re.search("^/", dl_link)) == True:
        data_parsed = urlparse(data_link)
        data_base = '://'.join([data_parsed.scheme, data_parsed.netloc])
        dl_link = ''.join([data_base, dl_link])
    else:
        pass
    # Find the states shape page on the dl page
    dl_req = Request(dl_link)
    dl_page = urlopen(dl_req)
    dl_soup = BeautifulSoup(dl_page, "lxml")
    for link in dl_soup.findAll('a'):
        if link.string is None:
            pass
        else:
            if bool(re.search("state shapefile", link.string, re.IGNORECASE)) == True:
                shp_link = link.get("href")
                break
            else:
                pass
    if bool(re.search("^/", shp_link)) == True:
        dl_parsed = urlparse(dl_link)
        dl_base = '://'.join([dl_parsed.scheme, dl_parsed.netloc])
        shp_link = ''.join([dl_base, shp_link])
    else:
        pass
    # Find the download links on the shapes page
    shp_req = Request(shp_link)
    shp_page = urlopen(shp_req)
    shp_soup = BeautifulSoup(shp_page, "lxml")
    tab = shp_soup.findAll("table")[0]
    shp_names = []
    shp_links = []
    for row in tab.findAll("tr"):
        for col in row.findAll("td"):
            for d in col.findAll("span"):
                shp_names.append(d.string)
                shp_links.append(d.get("data-url"))
    # Format output
    shp_parsed = urlparse(shp_link)
    shp_base = '://'.join([shp_parsed.scheme, shp_parsed.netloc])
    df = pd.DataFrame({"state":shp_names, "pad":shp_links})
    pad_final = []
    for i,row in df.iterrows():
        try:
            st = re.search("(?<=_state).*?(?=_shapefile)", row["state"], re.IGNORECASE).group(0)
        except:
            st = "NULL"
        if st == "NULL":
            pass
        else:
            print(st)
            if bool(re.search("^/", row["pad"])) == True:
                zip_link = ''.join([shp_base, row["pad"]])
            else:
                zip_link = row["pad"]
            zip_open = ZipFile(BytesIO(urlopen(zip_link).read()))
            zip_files = np.array(zip_open.namelist())
            shps = zip_files[np.where([bool(re.search(".shp$", f)) for f in zip_files])[0]]
            ft = [re.search("(?<=[0-9]{1}_[0-9]{1}).*?(?=(_state)|(.shp$))", x, re.IGNORECASE).group(0)
                  for x in shps]
            st_df = pd.DataFrame({"state_USPS":np.repeat(st, len(ft)),
                                  "PAD_type":ft,
                                  "PAD_file":shps,
                                  "PAD_link":np.repeat(zip_link, len(ft))})
            pad_final.append(st_df)
    # Return
    pad_concat = pd.concat(pad_final).reset_index(drop=True)
    return pad_concat



def read_pad(pad_link, pad_files):
    '''
    Read a PAD shapefile from its zip archive.

    Parameters
    ----------
    pad_link : str
        URL link to a PAD file zip archive.
    pad_files : str, or iterable of str
        File(s) within the archive at `pad_link` to load. If loading multiple
        files from the same archive, providing all files at once will save
        time reading.

    Returns
    -------
    geopandas.GeoDataFrame
        The PAD shape of interest. Will be a dict of GeoDataFrames if
        `pad_file` is an iterable, with `pad_file` serving as the keys.

    '''
    # Decide whether we're reading 1 file or many
    pad_zip = urlopen(pad_link).read()
    if isinstance(pad_files, str):
        pad_files = [pad_files]
        return_dict = False
    else:
        return_dict = True
        
    # Open the zip archive, then load from features. Can't use gpd.read_file
    # because there's currently no interplay between read_file and the output
    # of ZipFile or ZipMemoryFile
    pad_gdfs = {}
    with fiona.io.ZipMemoryFile(pad_zip) as pz:
        for pad_file in pad_files:
            with pz.open(pad_file) as pf:
                crs = pf.crs
                gdf = gpd.GeoDataFrame.from_features(pf, crs=crs)
            cols = [c for c in gdf.columns if c != "geometry"] + ["geometry"]
            gdf = gdf[cols]
            pad_gdfs[pad_file] = gdf
    if return_dict == True:
        return pad_gdfs
    else:
        return pad_gdfs[pad_files[0]]



# %% Example

# # Identify the currently available pad data
# DATA = pad_links_by_state()

# # Identify which shapes are available for a state of interest
# ST = "OR"
# state_data = DATA[DATA.state_USPS == ST]

# # Load all files for that state
# pad_state = read_pad(pad_link = state_data.PAD_link.iloc[0],
#                      pad_files = state_data.PAD_file)




