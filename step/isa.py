from . import osm

import re

from rdflib import URIRef, Namespace, Graph
from shapely import wkt
from shapely.ops import polygonize_full, cascaded_union
import geojson

import warnings
warnings.simplefilter('ignore')


def create_episodes(gpx, osn_graph, buffer_size, minimum_duration_ratio, minimum_length_ratio, keys, expand_keys):
    #points_data = gpx.get_points_data()
    #points = [(pdata.point.latitude, pdata.point.longitude) for pdata in points_data]

    excluded_keys = ['name', 'comment', 'source', 'boundary']
    expanded_keys = []

    # Search for tags in OSN
    #if 'osn_graph' not in locals():
    #    osn_graph = Graph()
    #    osn_graph.parse('../notebooks/osm_semantic_network.skos.rdf')

    #
    if expand_keys and len(keys) > 0:
        expanded_keys = []

        keys_regex = "|".join(keys)
        regex = r'"http://spatial.ucd.ie/lod/osn/term/k:({0}).*"'.format(keys_regex)

        query = """
        PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
        PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>

        SELECT ?subject ?relatedTerm ?lgdConcept
        {
         ?subject skos:related ?relatedTerm .
         ?relatedTerm skos:exactMatch ?lgdConcept .

         FILTER (REGEX(STR(?subject), """ + regex + """))
         FILTER (STRSTARTS(STR(?lgdConcept), "http://linkedgeodata.org/ontology"))
        }"""

        response = osn_graph.query(query)

        for row in response:
            uri = row[1]
            new_key = uri.split('k:')
            if len(new_key) > 1:
                new_key = new_key[-1]
            else:
                continue

            try:
                new_key = new_key.split('/')[0]
            except:
                pass

            if new_key not in keys:
                expanded_keys.append(new_key)

        expanded_keys = list(set(expanded_keys))

    # Simplify trajectory's shape and create a WKT representation of it:
    gpx_simple = gpx.clone()
    gpx_simple.simplify()

    linestring_simple = "LINESTRING("

    simple_points = gpx_simple.get_points_data()

    for i, point_data in enumerate(simple_points):
        point = point_data.point
        linestring_simple += str(point.longitude) + " " + str(point.latitude)
        if i < len(simple_points) - 1:
            linestring_simple += ", "

    linestring_simple += ")"

    # Using Overpass to retrieve OSM features:
    all_keys = keys + expanded_keys

    osm_features = osm.get_spatial_features(gpx, all_keys)
    print('Overpass response length: {0}'.format(len(osm_features)))

    # Cleaning the dataset to remove OSM features that do not have a tags with corresponding concepts in LGDO:
    osn_terms = []
    invalid_chars = [' ', '<', '>', '|', '"']

    if 'tags' in osm_features:
        for tags in osm_features['tags']:
            for item in tags.items():
                if item[0] not in excluded_keys and re.match('[a-z]*', item[0]) and re.match('[a-z]*', item[1]):
                    uri = "http://spatial.ucd.ie/lod/osn/term/k:{0}/v:{1}".format(item[0], item[1])
                    uri = ''.join([i if i not in invalid_chars else '_' for i in uri])
                    osn_terms.append("<{0}>".format(uri))
    else:
        return [], []

    query = """
    PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>

    SELECT ?osnConcept ?lgdoConcept
    {
    ?osnConcept skos:exactMatch ?lgdoConcept .

    FILTER (?osnConcept IN (""" + ", ".join(osn_terms) + """))
    FILTER (STRSTARTS(STR(?lgdoConcept), "http://linkedgeodata.org/ontology"^^xsd:string))
    }
    """

    response = osn_graph.query(query)

    valid_tags = []
    lgd_concepts = []
    for row in response:
        osn_concept = row[0]
        osn_concept = 'k:{0}'.format(osn_concept.split('k:')[-1])
        valid_tags.append(osn_concept)
        lgd_concepts.append(str(row[1]).split('/')[-1])

    print('{0} valid tags: {1}\ncorresponding to the LGD concepts: \n{2}'.format(
        len(valid_tags), valid_tags, lgd_concepts))

    # Exclude features that don't have the valid tags
    to_drop = []
    for tags, idx in zip(osm_features['tags'], osm_features.index):
        feature_tags = ['k:{0}/v:{1}'.format(item[0], item[1]) for item in tags.items()]
        if not any([tag in valid_tags for tag in feature_tags]):
            to_drop.append(idx)

    osm_features = osm_features.drop(to_drop)

    # Creating closed polygons with buffers:
    '''
    linestring = "LINESTRING("

    for i, point_data in enumerate(points_data):
        point = point_data.point
        linestring += str(point.longitude) + " " + str(point.latitude)
        if i < len(points_data) - 1:
            linestring += ", "

    linestring += ")"

    trajectory = wkt.loads(linestring)
    '''

    features = []
    features_json = []
    marker_data = []

    to_drop = []
    for item in osm_features.itertuples():
        try:
            feature0 = wkt.loads(item.geometry)
            json_feature0 = geojson.Feature(geometry=feature0, properties={"id": str(item.Index)})

            feature1 = feature0.buffer(buffer_size)
            json_feature1 = geojson.Feature(geometry=feature1)

            feature2 = polygonize_full(feature0)[0]
            json_feature2 = geojson.Feature(geometry=feature2)

            feature3 = cascaded_union([feature1, feature2])
            json_feature3 = geojson.Feature(geometry=feature3)

            # 0: original geometry (linestring)
            # 1: buffered 0 (polygon)
            # 2: polygonized
            # 3: union of 1 and 2
            # This is for visualization purposes.
            # A more efficient solution would be to buffer the polygonized line (feature2)
            features_json.append([json_feature0, json_feature1, json_feature2, json_feature3])
            features.append(feature3)

            rep_point = feature3.representative_point()
            popup_text = "{0}\n{1}".format(str(item.Index), repr(item.tags))
            if item.relation and len(item.relation) > 0:
                popup_text += " | part of: " + str(item.relation)
            marker_data.append(([rep_point.y, rep_point.x], popup_text))
        except Exception as e:
            # print(e)
            # print(item.Index)
            # print(item.label)
            # print(item.geometry)
            to_drop.append(item.Index)

    osm_features = osm_features.drop(to_drop)

    # Compute the intersections:
    feature_intervals = osm.compute_intersections(gpx, osm_features)

    groups = feature_intervals.groupby(level=0)

    # Select OSM features based on parameters:
    selected = []
    for group in groups:
        if group[1]['length_ratio'].sum() > minimum_length_ratio \
                or group[1]['duration_ratio'].sum() > minimum_duration_ratio:
            print('')
            print(group[0])
            print('relations:', osm_features.loc[group[0]]['relation'])
            print(osm_features.loc[group[0]]['label'], osm_features.loc[group[0]]['tags'])
            print("length ratio: {:.2f}%".format(group[1]['length_ratio'].sum() * 100))
            print("duration ratio: {:.2f}%".format(group[1]['duration_ratio'].sum() * 100))

            #selected.append(group[0])
            selected.append(group)

    return selected, osm_features
