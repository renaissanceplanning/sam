"""
Specialized downloader classes for different data types.

Provides concrete implementations of BaseDownloader for common patterns:
- HTTPDownloader: Simple file downloads
- ZipDownloader: ZIP archive processing
- GeoDataDownloader: GIS data (returns GeoDataFrame)
- RasterDownloader: Raster/imagery data (saves to file)
"""

from .http import HTTPDownloader
from .zip import ZipDownloader
from .geodata import GeoDataDownloader
from .raster import RasterDownloader

__all__ = [
    'HTTPDownloader',
    'ZipDownloader',
    'GeoDataDownloader',
    'RasterDownloader',
]
