# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 16:08:14 2022

@author: AZ7
"""

# %% Imports

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

from algi.raster import Raster
from algi import BBOX

# %% Globals for MRLC download

req = Request("https://www.mrlc.gov/data")
html_page = urlopen(req)
soup = BeautifulSoup(html_page, "lxml")
views_row = soup.findAll("div", class_="views-row")  # dataset elements
__NLCD__ = []
title_start = "[A-Z]{4} ([0-9]{4} |[A-Z]{4} )?(from-to |to )?([0-9]{4} )?([A-Z]{4} )?(High Resolution )?"
for vr in views_row:
    # Title
    try:
        title = vr.findAll("h2")[0].text
        ft = title
        title = title.strip()
        title = re.sub(r"\bImpervious\b", "Imperviousness", title)
        dst = (
            re.search("Land Cover|Imperviousness|Urban|Tree Canopy", title)
            .group(0)
            .lower()
        )
        if dst == "urban":
            dst = "imperviousness"
        else:
            pass
    except:
        continue
    # Geography (and title fix based off geography)
    geog = re.search(r"\((.*?)\)", title).group(0)
    title = re.sub(geog.replace("(", "\(").replace(")", "\)"), "", title)
    title = title.replace("Percent", "")
    title = re.sub(title_start, "", title)
    title = re.sub("^Imperviousness", "Developed Imperviousness", title)
    geog = re.sub(r"\(|\)", "", geog).lower()
    if bool(re.search("Zone 8", title)) == True:
        geog = geog + " zone 8"
        title = title.replace("Zone 8", "")
    else:
        pass
    title = re.sub(r"\s{2,}", " ", title).strip().lower()
    # Year
    region_year = vr.findAll("h3")[0].text
    region, year = region_year.split("|")
    year = re.sub(r"\s", "", year).strip()
    # Link
    link = vr.findAll("a", text="Download")[0]["href"]
    # Append info
    info = (dst, title, geog, year, link)
    __NLCD__.append(info)
__NLCD__ = pd.DataFrame(__NLCD__, columns=["family", "dataset", "geog", "year", "link"])
__ALL_YEARS__ = "2019,2016,2013,2011,2008,2006,2004,2001"

# %% Functions


def _find_nlcd(family=None, dataset=None, geog=None, year=None):
    """
    Find an NLCD land cover, developed imperviousness, or tree canopy dataset
    for a given geography and year.

    Parameters
    ----------
    family : str
        The NLCD dataset family: one of "land cover", "imperviousness", or
        "tree canopy". The default is None, in which case no filtering on
        family takes place.
    dataset : str, optional
        The dataset name. The default is None, in which case no filtering on
        dataset takes place.
    geog : str, optional
        The geography for the dataset: one of "conus" (lower 48), "alaska",
        "hawaii", or "puerto rico". The default is None, in which case no
        filtering on geography takes place.
    year : int or str, optional
        The year for the dataset. For change datasets, provide both years as
        strings separated by a ",", as in "year1,year2"; for "all years"
        datasets, set `year == "all"`; for single year datasets, provide the
        year as an integer or string. The default is None, in which case no
        filtering on year takes place.

    Notes
    -----
    To see all available NLCD datasets, run this function with the defaults.

    Returns
    -------
    pd.DataFrame
        All NLCD datasets that meet the specifications of the inputs.

    """
    # Find the family
    if family is None:
        df = __NLCD__.copy()
    else:
        fl = family.lower()
        if fl in __NLCD__.family.values:
            df = __NLCD__[__NLCD__.family == fl]
        else:
            raise ValueError(
                f"{family} is not an available NLCD dataset "
                "family; must be one of "
                f"{', '.join(__NLCD__.family.unique())}"
            )
    # Find the dataset
    if dataset is None:
        pass
    else:
        dl = dataset.lower()
        if dl in df.dataset.values:
            df = df[df.dataset == dl]
        else:
            raise ValueError(
                f"{dataset} is not an available NLCD dataset in "
                f"the {family} family; must be one of "
                f"{', '.join(np.sort(df.dataset.unique()))}"
            )
    # Set the geog
    if geog is None:
        gl = df.geog.unique()
    else:
        gl = geog.lower()
        if gl == "alaska":
            gl = ["alaska", "alaska zone 8"]
        else:
            gl = [gl]
    # Set the year
    if year is None:
        yl = df.year.unique()
    else:
        if year == "all":
            yl = [__ALL_YEARS__]
        else:
            yl = [re.sub(r"\{s}", "", str(year))]
    # Find the datasets matching the geog/year
    found = df[(df.geog.isin(gl)) & (df.year.isin(yl))]
    if len(found) > 0:
        return found
    else:
        available = "\n".join(["- " + g + ": " + y for g, y in zip(df.geog, df.year)])
        raise ValueError(
            f"{geog}/{year} is not available for the {dataset} "
            "dataset; the following are the available combos:\n"
            f"{available}"
        )


def _nlcd_raster_path_from_zip(zip_link):
    """
    Extract a rasterio-interpretable path to an NLCD raster from the zip file
    containing that raster.

    Parameters
    ----------
    zip_link : str
        URL to an NLCD zipped dataset.

    Returns
    -------
    str
        Download path for the raster; may be passed directly to
        `rasterio.open`.

    """
    req_zip_link = requests.get(zip_link, stream=True)
    zip_open = ZipFile(BytesIO(req_zip_link.content))
    zip_files = zip_open.namelist()
    ras = zip_files[np.where([bool(re.search(".img$", f)) for f in zip_files])[0][0]]
    full_link = "".join(["zip+", zip_link, "!", ras])
    return full_link


# TODO: make window a gpd.GeoDataFrame, add masking option
def dl_nlcd(dataset, geog, year, window=None, mask=False):
    """
    Download an NLCD dataset.

    Parameters
    ----------
    dataset : str
        NLCD dataset name.
    geog : str, optional
        The geography for the dataset: one of "conus" (lower 48), "alaska",
        "hawaii", or "puerto rico".
    year : int or str, optional
        The year for the dataset. For change datasets, provide both years as
        strings separated by a ",", as in "year1,year2"; for "all years"
        datasets, set `year = "all"`; for single year datasets, provide the
        year as an integer or string.
    window : gpd.GeoDataFrame or gpd.GeoSeries, optional
        The area in which to read the dataset; if provided, ONLY the portion
        of the raster within the bounding box of this geometry will be read.
        CRS conflicts will be resolved on the fly. The default is None, in
        which case the entire product is returned.
    mask : bool, optional
        If a window is provided, should the raster be masked to match the
        exact boundaries of the geometry? The default is False, in which case
        all values within the bounding box of the window will be represented
        in the raster. Ignored if `window is None`

    Returns
    -------
    algi.raster.Raster
        Raster of the NLCD product according to the input specifications

    """
    # Dataset, geog, and year uniquely identify datasets, so this will always
    # be one or zero rows. And if it's zero, it should fail in the function
    ds = _find_nlcd(family=None, dataset=dataset, geog=geog, year=year)
    # Warn the user if it's alaska zone 8
    if geog.lower() == "alaska" and ds.geog.iloc[0] == "alaska zone 8":
        warn("Note: this product only covers Alaska Zone 8")
    else:
        pass
    # Grab the link
    zip_link = ds.link.iloc[0]
    dl_link = _nlcd_raster_path_from_zip(zip_link=zip_link)
    # Load the raster
    if window is None:
        bboxobj = None
    elif isinstance(window, (gpd.GeoSeries, gpd.GeoDataFrame)):
        bboxobj = BBOX(window.total_bounds, window.crs)
    else:
        raise TypeError(
            "Expected gpd.GeoSeries or GeoDataFrame for " "'window'; got {type(window)}"
        )
    R = Raster.from_file(read_path=dl_link, window=bboxobj)
    # Mask if requested
    if window is None:
        return R.mask(geometry=window)
    else:
        return R


# %% Reference for writing rasters

# def _write_raster(from_file, to_file, dst_crs=None, window=None):
#     '''
#     Save a raster from a source file, optionally within a window geometry
#     and optionally with a transform from the source CRS

#     Parameters
#     ----------
#     from_file : str
#         Path to the source raster; must be parsable by `rasterio.open` in
#         mode "r"
#     to_file : str
#         Path for the output raster; must be parsable by `rasterio.open` in
#         mode "w"
#     dst_crs : anything accepted by `pyproj.crs.CRS.from_input()`, optional
#         A specification for a transform CRS. The default is None, in which
#         case no transformation is performed and the raster is saved in its
#         source CRS
#     window : geopandas GeoDataFrame or GeoSeries, optional
#         A geometry in which to read the raster; if provided, ONLY the portion
#         of the raster within the bbox of `window`
#         be cropped to the bounding box of `window` prior . The default is None.

#     Returns
#     -------
#     None.

#     '''
#     if window is None:
#         with rio.open(from_file) as src:
#             if dst_crs is None:
#                 kwargs = src.meta.copy()
#                 kwargs.update({"driver": "GTiff"})
#                 with rio.open(to_file, "w", **kwargs) as dst:
#                     dst.write(src)
#             else:
#                 dst_transform, dst_width, dst_height = calculate_default_transform(
#                     src.crs, dst_crs, src.width, src.height, *src.bounds
#                 )
#                 kwargs = src.meta.copy()
#                 kwargs.update({"driver": "GTiff", "transform": dst_transform,
#                                "width": dst_width, "height": dst_height,
#                                "crs": dst_crs})
#                 with rio.open(to_file, "w", **kwargs) as dst:
#                     reproject(source=rio.band(src, 1),
#                               destination=rio.band(dst, 1),
#                               src_transform=src.transform,
#                               src_crs=src.crs,
#                               dst_transform=dst_transform,
#                               dst_crs=dst_crs,
#                               resampling=Resampling.nearest)
#     else:
#         window_bbox = window.total_bounds
#         with rio.open(from_file) as src:
#             cw = src.window(*window_bbox)
#             src_trans = src.window_transform(cw)
#             if dst_crs is None:
#                 kwargs = src.meta.copy()
#                 kwargs.update({"driver": "GTiff", "transform": src_trans,
#                                "width": cw.width, "height": cw.height})
#                 with rio.open(to_file, "w", **kwargs) as dst:
#                     dst.write(src)
#             else:
#                 dst_transform, dst_width, dst_height = calculate_default_transform(
#                     src.crs, dst_crs, cw.width, cw.height, *window_bbox
#                 )
#                 kwargs = src.meta.copy()
#                 kwargs.update({"driver": "GTiff", "transform": dst_transform,
#                                "width": dst_width, "height": dst_height,
#                                "crs": dst_crs})
#                 with rio.open(to_file, "w", **kwargs) as dst:
#                     reproject(source=rio.band(src, 1),
#                               destination=rio.band(dst, 1),
#                               src_transform=src_trans,
#                               src_crs=src.crs,
#                               dst_transform=dst_transform,
#                               dst_crs=dst_crs,
#                               resampling=Resampling.nearest)
