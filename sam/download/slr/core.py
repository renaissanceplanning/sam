# -*- coding: utf-8 -*-
"""
Created on Tue Aug 29 10:39:10 2023

@author: w_rpg
"""

import os
import re
import requests
import geopandas as gpd
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
from urllib.request import Request, urlopen
from warnings import warn
from zipfile import ZipFile
from selenium import webdriver

from algi.raster import Raster
from algi import BBOX

# %% Site links

def _scrape_noaa_slr_dataset_links(message=True):
    '''
    Produce a table of dataset links available from the NOAA Sea Level Rise
    Data Download site

    Parameters
    ----------
    message : bool, optional
        Should progress be reported via printed messages? The default is True.

    Returns
    -------
    None.

    '''
    # Use selenium to grab the page source for the NOAA SLR data download site.
    # We have to use selenium because it puts things in an accordion using 
    # JavaScript, and `requests` can't expand those on the fly.
    driver = webdriver.Edge()
    driver.get("https://coast.noaa.gov/slrdata/")
    page_source = driver.page_source
    driver.close()
    # Convert the page to BeautifulSoup for parsing -- this allows us to use
    # standard parsing procedures
    soup = BeautifulSoup(page_source)
    # Links to NOAA SLR datasets (and relevant information) are stored in
    # panels of an accordion table -- so, pull all those panels.
    panels = soup.find_all(
        "div", 
        attrs={"class":"ng-scope ng-isolate-scope panel"}
    )
    # Iterate over the panels to extract dataset links and information
    n = len(panels)
    noaa_slr_links = []
    for i,panel in enumerate(panels):
        # The state/territory name is stored in the panel title -- so, pull the
        # panel title. We can index out using [0] because there's only 1 panel 
        # title per panel
        panel_title = panel.findAll(attrs={"class":"panel-title"})[0] 
        # The state/territory name is the text in the panel title
        state = panel_title.text.strip()
        if message:
            print(f"({i+1}/{n}) {state}")
        # Datasets may be split into sets of counties under the "ng-scope"
        # class -- so, pull all of those
        scopes = panel.findAll("div", attrs={"class":"ng-scope"})
        # Iterate over scopes to extract dataset links and information
        state_slr_links = []
        for scope in scopes:
            if scope.has_attr("ng-repeat"):
                # Counties are stored in an "ng-binding" class -- so, pull
                # that. We can index out using [0] because there's only of 
                # these per ng-scope
                ng_binding = scope.findAll(attrs={"class":"ng-binding"})[0]
                if message:
                    print(f"-- {ng_binding.text}")
                counties = [cty.strip() for cty in ng_binding.text.split(",")]
                # Dataset links are stored in a list in the panel -- so, pull 
                # all the list items in the panel
                list_items = scope.findAll("li")
                # Iterate over the list items to pull the dataset names and
                # links
                datasets = []
                links = []
                for item in list_items:
                    # The dataset name is the text in the the list item
                    dataset = ' '.join(item.text.strip().split())
                    datasets.append(dataset)
                    # The links are stored in the href attribute of the
                    # hyperlinks in the list item -- so, pull those. We can 
                    # index out using [0] because there's only hyperlink per 
                    # list item
                    link = item.findAll("a")[0]["href"]
                    links.append(link)
                # Create dataframe of links and datasets that is long on 
                # county, and append to master list for the state
                n_cty = len(counties)
                n_links = len(links)
                cty_slr_links = pd.DataFrame({
                    "county": np.repeat(counties, n_links),
                    "dataset": np.tile(datasets, n_cty),
                    "link": np.tile(links, n_cty)
                })
                state_slr_links.append(cty_slr_links)
        # Add state to the master dataframe and append to the master list for
        # the nation
        state_slr_links = pd.concat(state_slr_links)
        state_slr_links["state"] = state
        noaa_slr_links.append(state_slr_links)
    # Concat into a singular dataframe
    noaa_slr_links = pd.concat(noaa_slr_links)
    noaa_slr_links = noaa_slr_links[["state","county","dataset","link"]]
    return noaa_slr_links


# The links are to .zips -- iterate through to pull files
for url in noaa_slr_links.link:
    # If it's Sea Level Rise, Sea Level Rise Depth, Mapping Confidence, or
    # Flood Frequency, we're dealing with a .gdb. If it's DEM, we're 
    # dealing with a .tif.
    zip_link = f"https:{url}"
    req_zip_link = requests.get(zip_link, stream=True)
    zip_open = ZipFile(BytesIO(req_zip_link.content))
    zip_files = zip_open.namelist()
    zip_dirs = np.unique([os.path.dirname(f) for f in zip_files])
        



