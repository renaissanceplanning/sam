"""
LIHTC (Low Income Housing Tax Credit) data module.

Provides access to LIHTC property location and characteristics data.
"""

from .core import download_lihtc

__all__ = ['download_lihtc']
