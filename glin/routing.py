from matplotlib.pyplot import cm
import numpy as np
import osmnx as ox
import networkx as nx
import random
import pandas as pd
import pickle

__all__ = ["compute_paths"]

G_LOC = "G_map.pickle"

def get_G():

    try:
        G = pickle.load(open(G_LOC,"rb"))
    except:
        # Download the road network
        G = ox.graph_from_place('Bremen, Germany', network_type='drive')
        pickle.dump(G, open(G_LOC,"wb"))

    return G

def compute_paths(origin, endpoints):

    G = get_G()

    nodes = []
    for i in endpoints.values():
        nodes.append(ox.nearest_nodes(G, origin, i))

    route_list = []
    for i in nodes: 
        route = nx.shortest_path(G, i[0], i[1], weight='length')
        route_list.append(route)

    lengths = []
    for i in nodes:
        length = nx.shortest_path_length(G, i[0], i[1], weight='length')/1000 # m to Km
        lengths.append(length)

    zeros = np.zeros(1, len(lengths))

    return pd.DataFrame(list(zip(endpoints.keys(), list(range(1,len(lengths)+1)), lengths, zeros, lengths, zeros, zeros)), 
    columns =['BlobId', 'RouteId', 'TotalDistance','RailDistance', 'RoadDistance','PortDistance','AirDistance'])
