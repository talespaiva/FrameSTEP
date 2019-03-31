from step import isa

import os
import warnings

import gpxpy
from rdflib import Graph

warnings.simplefilter("ignore")

buffer_size = 0.0002 # ~20 meters
minimum_length_ratio = 0.2 #delta_s
minimum_duration_ratio = 0.2 #delta_t

keys = []#"leisure", "natural", "landuse"]
expand_keys = False

osn_graph = Graph()
osn_graph.parse('../notebooks/osm_semantic_network.skos.rdf')

all_groups, all_osm_features = [], []

for root, folder, files in os.walk('../notebooks/gpx'):
    for f in files:
        if '49996348-' in f:
            file_path = r'../notebooks/gpx/{0}'.format(f)
            print('\n########################################\n{0}'.format(file_path))
            gpx = gpxpy.parse(open(file_path, 'r'))

            groups, osm_features = isa.create_episodes(gpx,
                                                       osn_graph,
                                                       buffer_size,
                                                       minimum_duration_ratio,
                                                       minimum_length_ratio,
                                                       keys,
                                                       expand_keys)
            all_groups.append(groups)
            all_osm_features.append(osm_features)
