"""
LODES (Longitudinal Employer-Household Dynamics) data module.

Provides access to employment data including residence area characteristics (RAC),
workplace area characteristics (WAC), and origin-destination flows (OD).
"""

from .core import lodes

__all__ = ['lodes']
