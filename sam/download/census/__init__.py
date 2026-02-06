# Pure Python census downloads:
# - TIGER: Python (pygris)
# - ACS: Python (censusdata)
# - LODES: Python (direct download)
# R dependency fully removed as of 2026-02-04

from .core import *
from . import ref

# R version has been retired - using Python implementations only
HAS_R_CENSUS = False
