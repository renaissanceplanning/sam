# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 15:44:09 2022

@author: Aaron Weinstock
"""

import os
import pandana
import pickle
import networkx as nx
import numpy as np
import osmnx as ox

from sam.download.osm import dl_osm_network

# %% Globals

# TODO: hierarchies for highway types

_NODES_FIELDS_ = ["x", "y"]
_EDGES_FIELDS_ = ["u", "v", "key", "highway", "length", "speed_kph", "travel_time"]
_OBJ_TYPES_ = ["nx", "pandana", "gdf"]

# %% Helper Functions


def _dat_osm(geometry, net_type, add_travel_time=True, crs=None, **kwargs):
    """
    Download, Add travel time to, and Transform an OSM newtork.

    Parameters
    ----------
    geometry : gpd.GeoDataFrame or gpd.GeoSeries
        Area in which to download the network; all features should be
        [Multi]Polygon; passed to `dl_osm_network`.
    net_type : str
        The network type to download: "walk", "bike", or "drive"; passed to
        `dl_osm_network`.
    crs : Any, optional
        The CRS for the network; can be anything accepted by the
        `ox.project_graph()` function, e.g. an integer EPSG code. The
        default is None, in which case the projection is inherited from
        `geometry`.
    add_travel_time : bool
        Should a travel time attribute be added to the network? If True,
        the `ox.add_edge_speeds()` function will be used to add a speed to
        each edge, and the `ox.add_edge_travel_times()` function will be
        used to add a travel time to each edge. The default is True.
    kwargs:
        Keyword arguments to pass to `gary.trim_components` if trimming the
        downloaded osm network.

    Returns
    -------
    nx.MultiDiGraph

    """
    net = dl_osm_network(
        geometry=geometry, net_type=net_type, trim_components=False, **kwargs
    )
    if add_travel_time == True:
        net = ox.add_edge_speeds(net)
        net = ox.add_edge_travel_times(net)
    else:
        pass
    if crs is None:
        crs = geometry.TEST_CRS
    else:
        pass
    net = ox.project_graph(net, to_crs=crs)
    return net


# %% Class


class OSMNetwork(nx.MultiDiGraph):
    """
    Standardized downloader for OSM networks
    """

    def __init__(self, net):
        return super().__init__(net)

    @classmethod
    def walk(cls, geometry, add_travel_time=True, crs=None, **kwargs):
        """
        Download an OSM walk newtork.

        Parameters
        ----------
        see `sam.osm._dat_osm`

        Returns
        -------
        OSMNetwork (subclass of nx.MultiDiGraph)

        """
        net = _dat_osm(
            geometry=geometry,
            net_type="walk",
            add_travel_time=add_travel_time,
            crs=crs,
            **kwargs,
        )
        return cls(net)

    @classmethod
    def bike(cls, geometry, add_travel_time=True, crs=None, **kwargs):
        """
        Download an OSM walk newtork.

        Parameters
        ----------
        see `sam.osm._dat_osm`

        Returns
        -------
        OSMNetwork (subclass of nx.MultiDiGraph)

        """
        net = _dat_osm(
            geometry=geometry,
            net_type="bike",
            add_travel_time=add_travel_time,
            crs=crs,
            **kwargs,
        )
        return cls(net)

    @classmethod
    def drive(cls, geometry, add_travel_time=True, crs=None, **kwargs):
        """
        Download an OSM walk newtork.

        Parameters
        ----------
        see `sam.osm._dat_osm`

        Returns
        -------
        OSMNetwork (subclass of nx.MultiDiGraph)

        """
        net = _dat_osm(
            geometry=geometry,
            net_type="drive",
            add_travel_time=add_travel_time,
            crs=crs,
            **kwargs,
        )
        return cls(net)

    def to_gdf(self, trim=False):
        """
        Convert `OSMNetwork` from `nx.MultiDiGraph` to `gpd.GeoDataFrame`.

        Parameters
        ----------
        trim : bool
            Should attributes be trimmed for clarity? If yes, "nodes" will
            only retain x and y coordinate attributes, and "edges" will
            retain only highway type, length (in meters), speed (in kph, if
            present), and travel time (in seconds, if present). The default
            is False.

        Returns
        -------
        nodes : gpd.GeoDataFrame
            Nodes points, with the node ID as the index.
        edges : gpd.GeoDataFrame
            Edges lines, with the u/v/key as the index.

        """
        nodes, edges = ox.graph_to_gdfs(self)
        # TODO: hierarchy the highway types?
        edges = edges.reset_index().drop(columns="osmid")

        edges["highway"] = [
            "-".join(np.sort(hwy)) if isinstance(hwy, list) else hwy
            for hwy in edges.highway
        ]

        if trim == True:
            nf = [f for f in _NODES_FIELDS_ if f in nodes.columns]
            ef = [f for f in _EDGES_FIELDS_ if f in edges.columns]
            nodes = nodes[nf + ["geometry"]]
            edges = edges[ef + ["geometry"]]
        else:
            pass
        return (nodes, edges)

    # TODO: should we let gary handle this?
    def to_pandana(self):
        """
        Convert `OSMNetwork` from `nx.MultiDiGraph` to
        `pandana.network.Netowrk`.

        Returns
        -------
        pandana.network.Network
            Pandana network representation of the OSM network for routing.
            The network is loaded with "length" (in meters) and "travel_time"
            (in seconds, if present) as impedances.

        """
        nodes, edges = self.to_gdf()
        edges = edges.reset_index()
        imps = [f for f in ["length", "travel_time"] if f in edges.columns]
        return pandana.network.Network(
            node_x=nodes.x,
            node_y=nodes.y,
            edge_from=edges.u,
            edge_to=edges.v,
            edge_weights=edges[imps],
            twoway=False,
        )

    def to_shp(self, save_dir, prefix, trim=True):
        """
        Save `OSMNetwork` as nodes and edges shapefiles.

        Parameters
        ----------
        save_dir : path
            Directory in which to save the nodes and edges shapes. The nodes
            shape will be called "nodes.shp"; the edges shape will be called
            "edges.shp"
        trim : bool
            Should attributes be trimmed for clarity? If yes, "nodes" will
            retain a unique ID, along with x and y coordinate attributes;
            "edges" will retain u/v/key, highway type, length (in meters),
            speed (in kph, if present), and travel time (in seconds, if
            present). The default is False.

        Returns
        -------
        None.

        """
        nodes, edges = self.to_gdf(trim=trim)
        nodes_path = os.path.join(save_dir, f"{prefix}_nodes.shp")
        edges_path = os.path.join(save_dir, f"{prefix}_edges.shp")
        nodes.reset_index().to_file(nodes_path)
        edges.reset_index().to_file(edges_path)

    def to_pickle(self, save_path, obj_type="nx"):
        """
        Pickle an `OSMNetwork` in a given Python representation for easy
        reading in future python analyses.

        Parameters
        ----------
        save_path : path
            Save path for the pickled object.
        obj_type : TYPE, optional
            Representation of the network to be pickled. Options include "nx"
            (networkx graph), "gdf" (tuple of nodes and edges GeoDataFrames),
            or "pandana" (pandana network). The default is "nx".

        Returns
        -------
        None.

        """
        if obj_type == nx:
            obj = self.copy()
        elif obj_type == "gdf":
            obj = self.to_gdf()
        elif obj_type == "pandana":
            obj = self.to_pandana()
        else:
            raise ValueError(f"{obj_type} must be one of " f"{', '.join(_OBJ_TYPES_)}")
        with open(save_path, "wb") as dst:
            pickle.dump(obj, dst)
