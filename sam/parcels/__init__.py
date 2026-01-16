"""
Parcel data module.

Provides access to Florida Department of Revenue (DOR) parcel data.
"""

from .core import download_fl_parcels, download_old_fl_parcels

__all__ = ['download_fl_parcels', 'download_old_fl_parcels']
