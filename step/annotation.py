import rdflib
from rdflib import Namespace, URIRef
from model import step, utility, namespaces

import osm


def spatial_annotation(gpx, keys, minimum_length_ratio, minimum_duration_ratio):
    points_data = gpx.get_points_data()

    osm_features = osm.get_spatial_features(gpx, keys)

    #

    feature_intervals = osm.compute_intersections(gpx, osm_features)

    #

    groups = feature_intervals.groupby(level=0)

    #

    selected = []
    for group in groups:
        if group[1]['length_ratio'].sum() > minimum_length_ratio or \
                        group[1]['duration_ratio'].sum() > minimum_duration_ratio:
            tag_present = False
            for key in osm_features.loc[group[0]]['tags'].keys():
                if key in keys:
                    tag_present = True
                    continue

            if tag_present:
                selected.append(group[0])

    #

    OSNT = Namespace('http://spatial.ucd.ie/lod/osn/term/')
    LGDR = Namespace('http://linkedgeodata.org/triplify/')

    raw = utility.create_raw_trajectory(gpx)

    #

    foi_places = step.FeatureOfInterest("Places")

    for group in groups:
        if group[0] in selected:
            intervals = group[1]
            feature_id = group[0]

            semantics_str = 'near'
            if osm_features.loc[feature_id].label:
                semantics_str += ' ' + osm_features.loc[feature_id].label
            place_semantics = step.QualitativeDescription(semantics_str)

            if osm_features.loc[feature_id].relation is None:
                element_type = 'relation'
            else:
                element_type = 'way'

            osm_label = str(osm_features.loc[feature_id]['label'])

            related_tags = []
            for key, value in osm_features.loc[feature_id]['tags'].items():
                if key in keys:
                    related_tags.append(URIRef("{0}k:{1}/v:{2}".format(OSNT, key, value)))

            lgdo_uri = URIRef("{0}{1}{2}".format(LGDR, element_type, feature_id))

            contextual_element = step.ContextualElement(osm_label, lgdo_uri, related_tags)

            for item in intervals.itertuples():
                start_fix = raw.get_fix(points_data[item.start_index].point.time)
                end_fix = raw.get_fix(points_data[item.end_index].point.time)
                st_extent = step.SpatiotemporalExtent(start_fix, end_fix)

                episode = step.Episode(st_extent, place_semantics)
                episode.relate(contextual_element)

                foi_places.add_episode(episode)

    triples = foi_places.triplify()
    g = rdflib.Graph()
    g.bind('step', namespaces.STEP)
    g.bind('skos', namespaces.SKOS)
    g.bind('geo', namespaces.GEO)
    g.bind('time', namespaces.TIME)
    g.bind('owl', namespaces.OWL)

    for triple in triples:
        g.add(triple)

    return g