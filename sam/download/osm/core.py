"""
The `osm` module provides generalized methods to acquire network data
and building footprint polygons from Open Street Map. It depends on the `osmnx`
module to download and clean mode-specific networks.
"""

# %% Imports

import re
import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
from shapely.geometry import Polygon
from warnings import warn

import gary
from algi.dep.BBOX import BBOX
from osmnx._errors import ResponseStatusCodeError

# %% Globals

__OSMNX_NETWORK_BUILTINS__ = ["drive", "walk", "bike"]

# %% Functions


def dl_osm_network(
    geometry,
    net_type="drive",
    osm_query=None,
    trim_components=False,
    chunk_size=30000,
    **kwargs,
):
    """
    Download an OSM network for an area.

    Parameters
    ----------
    geometry : gpd.GeoDataFrame or gpd.GeoSeries
        The area in which the network will be downloaded. All features
        should be Polygons or MultiPolygons.
    net_type : str or None, optional
        A network type to download; OSM offers a number of different default
        queries for network types, including "drive", "walk", "bike", etc. One
        of this parameter and `osm_query` must be non-None. The default is
        "drive", which downloads a driving network.
    osm_query : str or None, optional
        A user-defined OSM query to be used to download the network. One of
        this parameter and `osm_query` must be non-None. If both this parameter
        and `net_type` are provided, this parameter will  override `net_type`.
        Use of this parameter should be reserved for special cases, and for
        users who are very familiar with OSM Overpass query structure; the
        default `net_types` will be sufficient in most cases. The default is
        None, which means the default `net_type` is used.
    trim_components : bool, optional
        Should connected components with just a few edges be removed from the
        final graph? This is most useful for non-motorized networks, which
        may feature small areas that provide no connectivity to the network
        as a whole. The default is False, in which case all components are
        returned as part of the network, regardless of size.
    chunk_size : int or float, optional
        The edge length for a square defining the maximum area to be covered by
        a single OSM query (in meters). OSM will automatically chunk any grabs
        greater than 50km-by-50km, so this parameter should be less than
        50,000. This parameter will not normally need to be adjusted. The
        default is 30000.
    **kwargs :
        passed to `gary.trim_components`; can include "min_edges" (an integer
        defining the minimum size in edges to retain a component) and/or
        "message" (a bool indicating whether or not to alert the user to the
        number of components removed). Ignored if `trim_components == False`.

    Notes
    -----
    The network covering `geometry` will be downloaded in chunks and composed
    into a single network. Chunks will be created by intersecting a
    `chunk_size x chunk_size` grid with the outer boundary of `geometry`,
    ensuring that (A) no individual chunk is too large and (B) the final
    network will match the boundaries of `geometry` exactly.

    Returns
    -------
    nx.MultiDiGraph
        The OSM network within `geometry`

    """
    # Check our inputs
    if isinstance(geometry, gpd.GeoDataFrame):
        pass
    elif isinstance(geometry, gpd.GeoSeries):
        geometry = gpd.GeoDataFrame({"geometry": geometry}, crs=geometry.crs)
    else:
        raise TypeError(
            "Expected gpd.GeoSeries or GeoDataFrame for "
            "'geometry'; got {type(geometry)}"
        )
    if isinstance(net_type, str) and isinstance(osm_query, str):
        net_type = "drive"
        warn("net_type and osm_query both provided; osm_query will override")
    elif isinstance(net_type, str) and osm_query is None:
        net_type = net_type.lower()
        if net_type in __OSMNX_NETWORK_BUILTINS__:
            pass
        else:
            raise ValueError(
                f"{net_type} is an invalid OSM network type; "
                "must be one of drive, walk, bike"
            )
    elif net_type is None and isinstance(osm_query, str):
        net_type = "drive"
    elif net_type is None and osm_query is None:
        raise ValueError("One of net_type and osm_query must be provided")
    else:
        if isinstance(net_type, (str, type(None))):
            n_msg = ""
        else:
            n_msg = f"Expected str or None for net_type, got {type(net_type)}"
        if isinstance(osm_query, (str, type(None))):
            o_msg = ""
        else:
            o_msg = f"Expected str or None for osm_query, got {type(osm_query)}"
        msg = re.sub(";$", "", "; ".join([n_msg, o_msg]).strip())
        raise TypeError(msg)
    if isinstance(trim_components, bool):
        pass
    else:
        raise TypeError(
            "Expected bool for trim_components, got " f"{type(trim_components)}"
        )
    if isinstance(chunk_size, (int, float)):
        if chunk_size > 50000:
            raise ValueError(
                "Chunk size exceeds OSM-recommended maximum; " "pick a value < 50,000"
            )
    else:
        raise TypeError("Expected numeric for chunk_size, got " f"{type(chunk_size)}")
    # Set the geom to 4326, and set up for chunking
    print("Organizing polygons for OSM query")
    if all(geometry.geom_type.isin(["Polygon", "MultiPolygon"])):
        pass
    else:
        raise TypeError("Non-polygon geometries present in geometry")
    avg_lng = geometry.to_crs(4326)["geometry"].representative_point().x.mean()
    utm_zone = int(np.floor((avg_lng + 180) / 6) + 1)
    utm_crs = f"+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    if len(geometry) == 1:
        geom_utm = geometry.to_crs(utm_crs)
    else:
        geometry["DISSOLVE"] = 1
        geom_utm = geometry.to_crs(utm_crs).dissolve(by="DISSOLVE")
    # builds a grid from top left corner of bbox
    bbox_utm = BBOX(geom_utm.total_bounds, geom_utm.crs)
    ncol = np.ceil((bbox_utm.xmax - bbox_utm.xmin) / chunk_size)
    nrow = np.ceil((bbox_utm.ymax - bbox_utm.ymin) / chunk_size)
    xstep = (bbox_utm.xmax - bbox_utm.xmin) / ncol
    ystep = (bbox_utm.ymax - bbox_utm.ymin) / nrow
    grid = []
    for i in range(int(ncol)):
        for j in range(int(nrow)):
            north = bbox_utm.ymax - ystep * j
            south = bbox_utm.ymax - ystep * (j + 1)
            east = bbox_utm.xmin + xstep * (i + 1)
            west = bbox_utm.xmin + xstep * i
            grid.append(
                Polygon([(west, north), (east, north), (east, south), (west, south)])
            )
    grid = gpd.GeoDataFrame({"geometry": grid}, crs=geom_utm.crs)
    chunks = gpd.overlay(grid, geom_utm, how="intersection").to_crs(4326)
    nchunks = len(chunks)
    # Grab the network
    nets = []
    print(f"Grabbing network in {nchunks} chunks")
    i = 1
    for c in chunks.geometry:
        print(f"-- chunk {i}/{nchunks}")
        # TODO: is setting truncate by edge=True good enough for composition?
        try:
            cg = ox.graph_from_polygon(
                c,
                network_type=net_type,
                simplify=True,
                retain_all=True,
                truncate_by_edge=True,
                clean_periphery=False,
                custom_filter=osm_query,
            )
            nets.append(cg)
            i += 1
        except ResponseStatusCodeError:
            pass

    # Compose network
    print("Composing and formatting networks")
    if len(nets) > 1:
        nf = nx.compose_all(nets)
    else:
        nf = nets[0]
    if trim_components == True:
        nf = gary.trim_components(graph=nf, **kwargs)
    else:
        pass
    return nf


# compose_distance (numeric): default=1609; if `iter_features=True`, how far should the
#         features be buffered to ensure all resulting networks overlap (in meters)?
#         Buffering guarantees no gaps in networks between individual features; the
#         default value should not need to be changed except in rare cases of areas with
#         long, uninterrupted road segments


def download_osm_buildings(geometry, polygons_only=True):
    """
    Download OSM buildings for an area.

    Parameters
    ----------
    geometry : gpd.GeoDataFrame or gpd.GeoSeries
        The area in which the buildigns will be downloaded. All features
        should be Polygons or MultiPolygons.
    polygons_only : bool, optional
        Should only building polygons be returned? The default is True.

    Notes
    -----
    Buildings can be represented as points or polygons in OSM, so the
    `polygons_only` flag can be used to remove point geometries for analyses
    that require building polygons. Additionally, not that OSM buildings are
    not guaranteed to be comprehensive, so the output dataset may not include
    ALL buildings in an area.

    Returns
    -------
    gpd.GeoDataFrame
        A shape of the buildings within `geometry`.

    """
    # Check our inputs
    if isinstance(geometry, gpd.GeoDataFrame):
        pass
    elif isinstance(geometry, gpd.GeoSeries):
        geometry = gpd.GeoDataFrame({"geometry": geometry}, crs=geometry.crs)
    else:
        raise TypeError(
            "Expected gpd.GeoSeries or GeoDataFrame for "
            "'geometry'; got {type(geometry)}"
        )
    if all(geometry.geom_type.isin(["Polygon", "MultiPolygon"])):
        pass
    else:
        raise TypeError("Non-polygon geometries present in geometry")
    if isinstance(polygons_only, bool):
        pass
    else:
        raise TypeError(
            "Expected bool for polygons_only, got " f"{type(polygons_only)}"
        )
    # Pull the buildings
    if len(geometry) == 1:
        geom_4326 = geometry.to_crs(4326)
    else:
        geometry["DISSOLVE"] = 1
        geom_4326 = geometry.dissolve(by="DISSOLVE").to_crs(4326)
    bld = ox.geometries_from_polygon(
        polygon=geom_4326.geometry.iloc[0], tags={"building": True}
    )
    # Drop non-polygon features if requested
    if polygons_only == True:
        bld = bld[bld.geom_type.isin(["Polygon", "MultiPolygon"])]
    else:
        pass
    return bld
