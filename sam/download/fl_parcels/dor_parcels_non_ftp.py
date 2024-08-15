import ftplib
import re
import pandas as pd
import numpy as np

import requests
from bs4 import BeautifulSoup

URL = r"https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL-DBF"

page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")