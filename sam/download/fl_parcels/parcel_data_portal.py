import re
import pandas as pd
import numpy as np
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, SoupStrainer
# Replacement for parcel_ftp.py as the DOR no longer uses a FTP

# Constants ------------------------------------------------------------------
base_nal_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL"
dbf_nal_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL-DBF"
gis_base_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data"
gis_2024_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/2024F/2024F%20PIN"
                # https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/2024F/2024F%20PIN/Alachua_2024Pin.zip
                # https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/2024F/2024F%20PIN/alachua_2024pin.zip

gis_file_name = "{county_name}_{year}Pin.zip"
nal_file_name = "{county_name}%20{county_number}%20Final%20NAL%20{year}.zip"

county_name = "Alachua"
year = 2024
print(gis_file_name.format(county_name=county_name, year=year))

# ----------------------------------------------------------------------------

## Eventually we will want to webscrape but for now just hardcoding the URLS

# def list_urls()

# ----------------------------------------------------------------------------

# Written by Aaron
def format_florida_counties(county):
    """
    produce all possible representations of a county name for the state of
    Florida (representations are case insensitive)

    Parameters
    ----------
    county : str
        county name

    Returns
    -------
    list of options for representing county names. in particular, spaces
    will be condensed to "_" or "", and the word "saint" will be tried as
    "saint", "st", and "st."
    """

    # First, FDOR refers to Miami-Dade as "Dade" only -- so if the name has
    # "Miami", call it dade
    if bool(re.search("miami", county, re.IGNORECASE)):
        county = "dade"

    # If theres a "Saint, St., or St" to start it, this is a different animal
    # because we have to consider all options. Otherwise, we really only
    # need to concern ourselves with spacing
    saint_search = "|".join(["^saint", "^st(\.) "])
    if bool(re.search(saint_search, county, re.IGNORECASE)):
        if bool(re.search("^saint", county, re.IGNORECASE)):
            rep = ["saint", "st", "st."]
        else:
            rep = ["saint ", "st ", "st. "]
        opts = [re.sub(saint_search, v, county, flags=re.IGNORECASE) for v in rep]
    else:
        opts = [county]

    # Spaces removed or as underscores
    sr = [o.replace(" ", "") for o in opts]
    su = [o.replace(" ", "_") for o in opts]
    spaced = opts + sr + su

    # Final options
    fo = np.unique(spaced).tolist()
    return fo


# ----------------------------------------------------------------------------

# Written by Aaron
def florida_counties():
    """
    produce a dataframe of Florida counties and all of their possible
    representations

    Returns
    -------
    pandas DataFrame with 4 columns:
        county: county name
        co_no: Florida DOR county number
        fips: 3-digit county FIPS code
        format: a possible representation of the county name (case insensitive)
    """

    # Florida counties
    fl = [
        "Alachua",
        "Baker",
        "Bay",
        "Bradford",
        "Brevard",
        "Broward",
        "Calhoun",
        "Charlotte",
        "Citrus",
        "Clay",
        "Collier",
        "Columbia",
        "Miami-Dade",
        "DeSoto",
        "Dixie",
        "Duval",
        "Escambia",
        "Flagler",
        "Franklin",
        "Gadsden",
        "Gilchrist",
        "Glades",
        "Gulf",
        "Hamilton",
        "Hardee",
        "Hendry",
        "Hernando",
        "Highlands",
        "Hillsborough",
        "Holmes",
        "Indian River",
        "Jackson",
        "Jefferson",
        "Lafayette",
        "Lake",
        "Lee",
        "Leon",
        "Levy",
        "Liberty",
        "Madison",
        "Manatee",
        "Marion",
        "Martin",
        "Monroe",
        "Nassau",
        "Okaloosa",
        "Okeechobee",
        "Orange",
        "Osceola",
        "Palm Beach",
        "Pasco",
        "Pinellas",
        "Polk",
        "Putnam",
        "St. Johns",
        "St. Lucie",
        "Santa Rosa",
        "Sarasota",
        "Seminole",
        "Sumter",
        "Suwannee",
        "Taylor",
        "Union",
        "Volusia",
        "Wakulla",
        "Walton",
        "Washington",
    ]

    # DOR county codes
    cono = [str(x) for x in np.arange(11, 78).tolist()]

    # FIPS
    fips = (
        np.arange(1, 24, 2).tolist()
        + [86]
        + np.arange(27, 86, 2).tolist()
        + np.arange(87, 134, 2).tolist()
    )
    fips = [str(f).zfill(3) for f in fips]

    # Iterate through names and create representations
    df = []
    for i in range(len(fl)):
        df.append(
            pd.DataFrame(
                {
                    "county": fl[i],
                    "co_no": cono[i],
                    "fips": fips[i],
                    "format": format_florida_counties(fl[i]),
                }
            )
        )
    df = pd.concat(df)

    # Done
    return df


fl_co = florida_counties()

# ----------------------------------------------------------------------------

# Written by Aaron
def extract_year(url, regex="[0-9]{4}"):
    """
    extract a year from a url string

    Parameters
    ----------
    url : str
        url to a data file
    regex : str
        regular expression to find a year. The default is `[0-9]{4}`, or 4
        numbers in a row (which works for the Florida DOR FTP site)

    Returns
    -------
    The FIRST year found; if the regex might find more than 1 unique year,
    consider a different regex
    """

    # If you find a year, return it as an integer. If there isn't one, return
    # a null value of 9999
    try:
        year = re.findall(regex, url)[0]
        year = int(year)
    except:
        year = 9999
    return year


# ----------------------------------------------------------------------------

# Written by Aaron
def extract_county_name(url, regex):
    """
    extract a florida county name from a url string

    Parameters
    ----------
    url : str
        url to a data file
    regex : str
        regular expression to find a county

    Returns
    -------
    The FIRST county found; if the regex might find more than 1 unique county,
    consider a different regex
    """

    # If you find a county, return it as an string. If there isn't one, return
    # a null value of ''
    try:
        county = re.findall(regex, url, re.IGNORECASE)[0]
    except:
        county = ""
    return county


# ----------------------------------------------------------------------------

def extract_county_number(url):
    """
    extract a Florida DOR county from a url string

    Parameters
    ----------
    url : str
        url to a data file

    Returns
    -------
    The FIRST county number found; if the regex might find more than 1 unique
    county, consider a different regex
    """

    # If you find a number, return it as an string. If there isn't one, return
    # a null value of ''
    co_nos = [str(x) for x in np.arange(11, 78, 1).tolist()]

    county = re.findall("\D[0-9]{2}\D", url)
    if county != []:
        county = [re.findall("[0-9]{2}", x)[0] for x in county]
        county = [x for x in county if x in co_nos]
        try:
            county = county[0]
        except:
            county = ""
    else:
        county = ""
    return county


# ----------------------------------------------------------------------------

def build_url(county, year):
    if type(county) != str:
        raise TypeError("county must be type str")
    
    formatted_names = format_florida_counties(county=county)
    
    county_name = fl_co.loc[fl_co.format.isin(formatted_names), "format"].item()
    county_number = fl_co.loc[fl_co.format.isin(formatted_names), "co_no"].item()
    
    if year == 2024:
        gis_url = f"{gis_2024_url}/{gis_file_name.format(county_name=county_name,year=year)}"
    else:
        gis_url = f"{gis_base_url}/{year}F/{gis_file_name.format(county_name=county_name,year=year)}"
    nal_url = f"{base_nal_url}/{year}F/{nal_file_name.format(county_name=county_name, county_number=county_number,year=year)}"
    return gis_url, nal_url

# ----------------------------------------------------------------------------

if __name__ == "__main__":
    gis_url, nal_url = build_url(county_name, year)
    
    print(nal_url)
    # print(gis_url)
    
    from pprint import pprint
    import geopandas as gpd
    
    pprint(gpd.read_file(gis_url))
    pprint(pd.read_csv(nal_url))