# -*- coding: utf-8 -*-
"""
Overture Maps Places (POI) downloader.

Downloads point-of-interest data from Overture Maps via DuckDB, querying
GeoParquet files on S3 directly. Requires DuckDB >= 1.1.0 with the
spatial and httpfs extensions.

Install dependencies:
    pip install duckdb geopandas

Schema reference (v2.0.0):
    https://docs.overturemaps.org/schema/reference/places/place/
"""

import logging
from typing import Optional, Union

import duckdb
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

logger = logging.getLogger(__name__)

# S3 bucket and path pattern
_S3_BUCKET = "overturemaps-us-west-2"
_S3_REGION = "us-west-2"
_DEFAULT_RELEASE = "2026-11-18.0"
_PLACES_PATH = "theme=places/type=place/*"


def _get_connection() -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection with spatial and httpfs extensions loaded."""
    db = duckdb.connect()
    db.execute("""
        INSTALL spatial;
        INSTALL httpfs;
        LOAD spatial;
        LOAD httpfs;
        SET s3_region='us-west-2';
    """)
    return db


def _bbox_from_geometry(geometry) -> tuple:
    """
    Extract a bounding box from a GeoDataFrame, GeoSeries, or shapely geometry.

    Returns (xmin, ymin, xmax, ymax) in WGS84.
    """
    if isinstance(geometry, (gpd.GeoDataFrame, gpd.GeoSeries)):
        geom_wgs84 = geometry.to_crs("EPSG:4326")
        return tuple(geom_wgs84.total_bounds)
    else:
        return geometry.bounds


def download_overture_places(
    geometry: Union[gpd.GeoDataFrame, gpd.GeoSeries],
    release: str = _DEFAULT_RELEASE,
    min_confidence: float = 0.0,
    category: Optional[str] = None,
    exclude_closed: bool = True,
    clip: bool = True,
) -> gpd.GeoDataFrame:
    """
    Download Overture Maps Places (POI) data for a study area.

    Queries Overture GeoParquet on S3 via DuckDB, filtering by bounding box
    and optionally by category and confidence. Returns a GeoDataFrame of
    point features.

    Parameters
    ----------
    geometry : GeoDataFrame or GeoSeries
        Study area boundary. Will be reprojected to WGS84 for the bbox query.
    release : str, optional
        Overture release tag (default: current release).
    min_confidence : float, optional
        Minimum confidence score, 0.0 to 1.0 (default: 0.0, no filter).
    category : str or None, optional
        Filter to a specific basic_category value (case-insensitive).
        Pass None for all categories.
    exclude_closed : bool, optional
        Exclude permanently closed places (default: True).
    clip : bool, optional
        Clip results to the actual geometry boundary, not just the bounding
        box (default: True).

    Returns
    -------
    gpd.GeoDataFrame
        Point features with columns: id, name, basic_category, confidence,
        operating_status, websites, phones, addresses, geometry.

    Examples
    --------
    >>> study_area = gpd.read_file("study_area.shp")
    >>> places = download_overture_places(study_area)
    >>> restaurants = download_overture_places(study_area, category="restaurant")
    """
    xmin, ymin, xmax, ymax = _bbox_from_geometry(geometry)
    parquet_path = (
        f"s3://{_S3_BUCKET}/release/{release}/{_PLACES_PATH}"
    )

    logger.info(
        f"Querying Overture Places (release={release}) "
        f"bbox=({xmin:.4f}, {ymin:.4f}, {xmax:.4f}, {ymax:.4f})"
    )

    where_clauses = [
        f"bbox.xmin >= {xmin}",
        f"bbox.xmax <= {xmax}",
        f"bbox.ymin >= {ymin}",
        f"bbox.ymax <= {ymax}",
    ]

    if min_confidence > 0:
        where_clauses.append(f"confidence >= {min_confidence}")

    if exclude_closed:
        where_clauses.append(
            "operating_status IS NULL OR operating_status != 'permanently_closed'"
        )

    if category:
        where_clauses.append(f"LOWER(basic_category) = LOWER('{category}')")

    where_sql = " AND ".join(f"({c})" for c in where_clauses)

    query = f"""
        SELECT
            id,
            names.primary AS name,
            basic_category,
            confidence,
            operating_status,
            websites[1] AS website,
            phones[1] AS phone,
            geometry
        FROM read_parquet('{parquet_path}', filename=true, hive_partitioning=1)
        WHERE {where_sql}
    """

    db = _get_connection()
    logger.info("Executing DuckDB query against Overture S3...")
    df = db.execute(query).df()
    db.close()

    if df.empty:
        logger.warning("No places found for the given area and filters.")
        return gpd.GeoDataFrame(
            columns=["id", "name", "basic_category", "confidence",
                     "operating_status", "website", "phone", "geometry"],
            geometry="geometry",
            crs="EPSG:4326",
        )

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkb(df["geometry"].apply(bytes)),
        crs="EPSG:4326",
    )

    logger.info(f"Downloaded {len(gdf)} places from Overture")

    if clip and isinstance(geometry, (gpd.GeoDataFrame, gpd.GeoSeries)):
        mask = geometry.to_crs("EPSG:4326")
        if isinstance(mask, gpd.GeoSeries):
            mask = gpd.GeoDataFrame(geometry=mask)
        gdf = gpd.clip(gdf, mask)
        logger.info(f"Clipped to {len(gdf)} places within study area")

    return gdf


def list_overture_categories(
    geometry: Union[gpd.GeoDataFrame, gpd.GeoSeries],
    release: str = _DEFAULT_RELEASE,
) -> pd.DataFrame:
    """
    List available Overture place categories within a study area.

    Useful for exploring what category values are present before filtering.

    Parameters
    ----------
    geometry : GeoDataFrame or GeoSeries
        Study area boundary.
    release : str, optional
        Overture release tag.

    Returns
    -------
    pd.DataFrame
        Columns: basic_category, count. Sorted by count descending.
    """
    xmin, ymin, xmax, ymax = _bbox_from_geometry(geometry)
    parquet_path = (
        f"s3://{_S3_BUCKET}/release/{release}/{_PLACES_PATH}"
    )

    query = f"""
        SELECT
            basic_category,
            COUNT(*) as count
        FROM read_parquet('{parquet_path}', filename=true, hive_partitioning=1)
        WHERE
            bbox.xmin >= {xmin} AND
            bbox.xmax <= {xmax} AND
            bbox.ymin >= {ymin} AND
            bbox.ymax <= {ymax}
        GROUP BY basic_category
        ORDER BY count DESC
    """

    db = _get_connection()
    result = db.execute(query).df()
    db.close()

    logger.info(f"Found {len(result)} unique categories in area")
    return result
