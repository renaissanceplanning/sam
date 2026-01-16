"""
NLCD data manipulation and analysis.

This module provides tools for working with National Land Cover Database
rasters after they've been downloaded.
"""

from .core import NLCD, NLCD_CLASSES, DEVELOPED_RECLASSIFICATION, NATURAL_RECLASSIFICATION

from sam.download.nlcd import download_nlcd

__all__ = ['NLCD', 'NLCD_CLASSES', 'DEVELOPED_RECLASSIFICATION', 'NATURAL_RECLASSIFICATION', download_nlcd]