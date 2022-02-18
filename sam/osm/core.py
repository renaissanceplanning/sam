# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 15:44:09 2022

@author: Aaron Weinstock
"""

import os
import pandana
import pickle
import networkx as nx
import osmnx as ox
from pyproj import CRS

from rputils.download.osm import dl_osm_network #TODO environment is broke my guy

# %% Globals

# TODO: hierarchies for highway types

_NODES_FIELDS_ = ["x","y"]
_EDGES_FIELDS_ = ["highway","minutes","miles"]
_OBJ_TYPES_ = ["nx","pandana","gdf"]

# %% Functions

class osm_network(nx.MultiDiGraph):
    '''
    Standardized downloader for OSM networks
    '''
    def __init__(self, net):
        return super().__init__(net)
    
    @classmethod
    def osm_walk(geometry, crs=None, add_speed=True):
        '''
        Download an OSM walk newtork.

        Parameters
        ----------
        geometry : gpd.GeoDataFrame or gpd.GeoSeries
            Area in which to download the network; all features should be
            [Multi]Polygon.
        crs : Any, optional
            The CRS for the network; can be anything accepted by the
            `ox.project_graph()` function, e.g. an integer EPSG code. The 
            default is None, in which case the projection is inherited from
            `geometry`.
        add_speed : bool
            Should a speed attribute be added to the network? If True, the
            `ox.add_edge_speeds()` function will be used to add a speed to
            each edge.

        Returns
        -------
        nx.MultiDiGraph

        '''
        net = dl_osm_network(geometry=geometry,
                             net_type="walk",
                             trim_components=True)
        if crs is None:
            crs = geometry.crs
        else:
            pass
        net = ox.project_graph(net, to_crs=crs)
        net = ox.add_edge_speeds(net)
    
    def to_gdf(self):
        '''
        Standardized conversion of OSM network from `nx.MultiDiGraph` to
        `gpd.GeoDataFrame`.

        Returns
        -------
        nodes : gpd.GeoDataFrame
            Nodes points, with the node ID as the index, and attributes
            x and y giving the coordinates.
        edges : gpd.GeoDataFrame
            Edges lines, with the u/v/key as the index, and attributes
            highway (facility type), minutes (link travel time in minutes),
            and miles (link length in miles).

        '''
        net = ox.add_edge_speeds(self)
        nodes, edges = ox.graph_to_gdfs(net)
        nodes = nodes[_NODES_FIELDS_+["geometry"]]
        edges["miles"] = edges["length"] / 1609.34
        edges["minutes"] = edges["length"] / 1000 / edges["speed_kph"] * 60
        edges = edges[_EDGES_FIELDS_+["geometry"]]
        # TODO: either string the highway type or apply hierarchies
        return (nodes, edges)
    
    # TODO: should we let gary handle this?
    def to_pandana(self):
        '''
        Standardized conversion of OSM network from `nx.MultiDiGraph` to
        `pandana.network.Network`.

        Returns
        -------
        pandana.network.Network
            Pandana network representation of the OSM network for routing.
            The network is loaded with "minutes" and "miles" attributes as
            impedances.

        '''
        nodes, edges = self.to_gdf()
        edges = edges.reset_index()
        return pandana.network.Network(node_x=nodes.x,
                                       node_y=nodes.y,
                                       edge_from=edges.u,
                                       edge_to=edges.v,
                                       edge_weights=edges[["minutes","miles"]],
                                       twoway=False)
                                   
    def to_shp(self, save_dir):
        '''
        Write standardized versions of OSM nodes and edges to shapefile.
        
        The nodes and edges will be written with the attributes defined
        in the `to_gdf` method.

        Parameters
        ----------
        save_dir : path
            Directory in which to save the nodes and edges shapes. The nodes
            shape will be called "nodes.shp"; the edges shape will be called
            "edges.shp"

        Returns
        -------
        None.

        '''
        nodes, edges = self.to_gdf()
        nodes_path = os.path.join(save_dir, "nodes.shp")
        edges_path = os.path.join(save_dir, "edges.shp")
        nodes.reset_index().to_file(nodes_path)
        edges.reset_index().to_file(edges_path)
        return None
    
    def to_pickle(self, save_path, obj_type="nx"):
        '''
        Save a standardized OSM network in a given representation as a pickle
        file, for easy reading in future python analyses

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

        '''
        if obj_type == nx:
            obj = self
        elif obj_type == "gdf":
            obj = self.to_gdf()
        elif obj_type == "pandana":
            obj = self.to_pandana()
        else:
            raise ValueError(f"{obj_type} must be one of "\
                             f"{', '.join(_OBJ_TYPES_)}")
        with open(save_path, "wb") as dst:
            pickle.dump(obj, dst)
        return None
        
    
    
        
    
    
    
    