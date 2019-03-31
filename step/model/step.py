from abc import ABCMeta, abstractmethod
from rdflib import RDF, RDFS, XSD, URIRef, Namespace, Literal, OWL
import shortuuid
from .namespaces import STEP, TIME, SF, GEO, SKOS, EXAMPLE


class Resource(object):
    #metaclass_ = ABCMeta

    def __init__(self, label=None, uri=None):
        self.label = label
        if uri:
            self._uri = URIRef(uri)
        else:
            self._uri = URIRef(''.join([EXAMPLE, shortuuid.uuid()[:8]]))

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value):
        self._uri = value

    def __repr__(self):
        return '"Resource": {{ "label": "{0}" }}'.format(self.label)

    #@abstractmethod
    def triplify(self):
        type_tuple = []
        if type(self) == Resource:
            type_tuple.add((self._uri, RDF.type, RDFS.Resource))

        member_triples = []
        if self.label:
            member_triples += [(self._uri, RDFS.label, Literal(self.label, datatype=XSD.string))]

        return type_tuple + member_triples


class Agent(Resource):
    def __init__(self, label):
        super(Agent, self).__init__(label)
        self.trajectories = []


class Trajectory(Resource):
    def __init__(self, label, raw_trajectory):
        super(Trajectory, self).__init__(label)
        self.raw_trajectory = raw_trajectory
        self.features_of_interest = []

    def triplify(self):
        return super(Trajectory, self).triplify() + [
            (self._uri, RDF.type, STEP.Trajectory)
        ]


class FeatureOfInterest(Resource):
    def __init__(self, label):
        super(FeatureOfInterest, self).__init__(label)
        self.episodes = []

    def add_episode(self, episode):
        if isinstance(episode, Episode):
            self.episodes.append(episode)
        else:
            raise Exception('Episode expected')

    def __repr__(self):
        return '{{ "FeatureOfInterest": {{ "label": "{0}", "Episodes": {1} }} }}'.format(self.label, self.episodes)

    def triplify(self):
        episode_triples = []
        for episode in self.episodes:
            episode_triples.append((self._uri, STEP.hasEpisode, episode.uri))
            episode_triples += episode.triplify()

        return super(FeatureOfInterest, self).triplify() + [
            (self._uri, RDF.type, STEP.FeatureOfInterest)
        ] + episode_triples


class ContextualElement(Resource):
    def __init__(self, label=None, same_as=None, related=None):
        super(ContextualElement, self).__init__(label)
        self.features_of_interest = []
        self.related = related
        self.same_as = same_as

    def __repr__(self):
        label_str = '"label": "{0}"'.format(self.label)
        features_of_interest_str = ', "FeaturesOfInterest": {0}'.format(self.features_of_interest)
        same_as_str = ', "same_as": "{0}"'.format(self.same_as)
        related_str = ', "related": {0}'.format(self.related)

        return '"ContextualElement": {{ {label}{fois}{same_as}{related} }}'.format(label=label_str if self.label else '',
                                                                                fois=features_of_interest_str if self.features_of_interest else '',
                                                                                same_as=same_as_str if self.same_as else '',
                                                                                related=related_str if self.related else '')

    def triplify(self):
        features_of_interest_triples = []
        for feature in self.features_of_interest:
            features_of_interest_triples.append(feature.triplify())

        relates_triples = []
        if self.related:
            for related_uri in self.related:
                relates_triples.append((self._uri, SKOS.related, URIRef(related_uri)))

        same_as_triple = []
        if self.same_as:
            same_as_triple = [(self._uri, OWL.sameAs, URIRef(self.same_as))]

        return super(ContextualElement, self).triplify() + [
            (self._uri, RDF.type, STEP.ContextualElement)
        ] + features_of_interest_triples + relates_triples + same_as_triple

class Episode(Resource):
    def __init__(self, extent, semantic_description, label=None):
        super(Episode, self).__init__(label)
        self.extent = [extent]
        self.semantic_description = semantic_description
        self.relates_to = None

    def relate(self, contextual_element):
        self.relates_to = contextual_element

    def add_extent(self, new_extent):
        self.extent.append(new_extent)

    def __repr__(self):
        return '{{ "Episode": {{ "semantic_description":{0}, "extent": {1}, "relates_to": {2} }} }}'.format(self.semantic_description, self.extent, self.relates_to)

    def triplify(self):
        member_triples = []

        if len(self.extent) > 0:
            for ext in self.extent:
                member_triples.append((self._uri, STEP.hasExtent, ext.uri))
                member_triples += ext.triplify()

        if self.semantic_description:
            member_triples.append((self._uri, STEP.hasSemanticDescription, self.semantic_description.uri))
            member_triples += self.semantic_description.triplify()

        if self.relates_to:
            member_triples.append((self._uri, STEP.relatesTo, self.relates_to.uri))
            member_triples += self.relates_to.triplify()

        return super(Episode, self).triplify() + [
            (self._uri, RDF.type, STEP.Episode)
        ] + member_triples


class SemanticDescription(Resource):
    def __init__(self):
        super(SemanticDescription, self).__init__()

    def triplify(self):
        type_tuple = []
        if type(self) == SemanticDescription:
            type_tuple.add((self._uri, RDF.type, STEP.SemanticDescription))

        return super(SemanticDescription, self).triplify() + type_tuple


class QualitativeDescription(SemanticDescription):
    def __init__(self, description):
        super(QualitativeDescription, self).__init__()
        self.description = description

    def __repr__(self):
        return '{{ "QualitativeDescription": {{ "description": "{0}"}} }}'.format(self.description)

    def triplify(self):
        return super(QualitativeDescription, self).triplify() + [
            (self._uri, RDF.type, STEP.QualitativeDescription),
            (self._uri, RDF.value, Literal(self.description, datatype=XSD.string))
            # TODO: assuming a literal value, but this can be extended to a domain-specific ontology
        ]


class QuantitativeValue(SemanticDescription):
    def __init__(self, value, unit):
        super(QuantitativeValue, self).__init__()
        self.value = value
        self.unit = unit

    def __repr__(self):
        return '{{ "QuantitativeValue": {{ "value": "{0}", "unit": "{1}"}} }}'.format(self.value, self.unit)

    def triplify(self):
        return super(QuantitativeValue, self).triplify() + [
            (self._uri, RDF.type, STEP.QuantitativeValue),
            (self._uri, RDF.value, Literal(self.value, datatype=XSD.string)),
            (self._uri, STEP.hasUnit, Literal(self.unit, datatype=XSD.string)) # TODO
        ]


class Extent(Resource):
    def __init__(self):
        super(Extent, self).__init__()

    def triplify(self):
        type_tuple = []
        if type(self) == Extent:
            type_tuple.add((self._uri, RDF.type, STEP.Extent))

        return super(Extent, self).triplify() + type_tuple

class SpatialExtent(Extent):
    def __init__(self):
        super(SpatialExtent, self).__init__()

    def triplify(self):
        type_tuple = []
        if type(self) == SpatialExtent:
            type_tuple.add((self._uri, RDF.type, STEP.SpatialExtent))

        return super(SpatialExtent, self).triplify() + type_tuple


class TemporalExtent(Extent):
    def __init__(self):
        super(TemporalExtent, self).__init__()

    def triplify(self):
        type_tuple = []
        if type(self) == TemporalExtent:
            type_tuple.add((self._uri, RDF.type, STEP.TemporalExtent))

        return super(TemporalExtent, self).triplify() + type_tuple


# { Based on OWL:Time
class TemporalEntity(TemporalExtent):
    def __init__(self):
        super(TemporalEntity, self).__init__()

    def triplify(self):
        type_tuple = []
        if type(self) == TemporalEntity:
            type_tuple.add((self._uri, RDF.type, TIME.TemporalEntity))

        return super(TemporalEntity, self).triplify() + type_tuple


class TimeInstant(TemporalEntity):
    def __init__(self, in_datetime):
        super(TimeInstant, self).__init__()
        self.in_datetime = in_datetime

    def __repr__(self):
        return '"TimeInstant": {{ "in_datetime": "{0}"}}'.format(self.in_datetime)

    def triplify(self):
        return super(TimeInstant, self).triplify() + [
            (self._uri, RDF.type, TIME.Instant),
            (self._uri, TIME.inXSDDateTime, Literal(self.in_datetime, datatype=XSD.dateTime))
        ]


class TimeInterval(TemporalEntity):
    def __init__(self, beginning, end):
        super(TimeInterval, self).__init__()
        self.beginning = beginning
        self.end = end

    def __repr__(self):
        return '"TimeInterval": {{ "beginning": {0}, "end": {1}}}'.format(self.beginning, self.end)

    def triplify(self):
        return super(TimeInterval, self).triplify() + [
            (self._uri, RDF.type, TIME.Interval),
            (self._uri, TIME.hasBeginning, self.beginning.uri),
            (self._uri, TIME.hasEnd, self.end.uri)
        ] + self.beginning.triplify() + self.end.triplify()
# }


class SpatiotemporalExtent(Extent):
    def __init__(self, starting_point, ending_point=None):
        super(SpatiotemporalExtent, self).__init__()
        self.key_points = []
        self.starting_point = starting_point
        self.ending_point = ending_point

    def __repr__(self):
        return '{{ "SpatiotemporalExtent": {{ "start": {0}, "end": {1}, "key_points": {2}}} }}'.format(self.starting_point, self.ending_point, self.key_points)

    def triplify(self):
        key_point_tuples = []
        for kp in self.key_points:
            key_point_tuples.append(kp.triplify())

        return super(SpatiotemporalExtent, self).triplify() + [
            (self._uri, RDF.type, STEP.SpatiotemporalExtent),
            (self._uri, STEP.hasStartingPoint, self.starting_point.uri),
            (self._uri, STEP.hasEndingPoint, self.ending_point.uri),
        ] + self.starting_point.triplify() + self.ending_point.triplify() + key_point_tuples


class KeyPoint(Resource):
    def __init__(self, location, instant):
        super(KeyPoint, self).__init__()
        self.location = location
        self.time = instant

    def triplify(self):
        return super(KeyPoint, self).triplify() + [
            (self._uri, RDF.type, STEP.KeyPoint),
            (self._uri, STEP.hasLocation, self.location.uri),
            (self._uri, STEP.atTime, self.instant.uri)
        ] + self.location.triplify() + self.time.triplify()


class RawTrajectory(Resource):
    def __init__(self):
        super(RawTrajectory, self).__init__()
        self.fixes = []

    def get_fix(self, timestamp):
        for fix in self.fixes:
            if fix.instant.in_datetime == timestamp:
                return fix

    def triplify(self):
        fix_tuples = []
        for fix in self.fixes:
            fix_tuples.append(fix.triplify())

        return super(RawTrajectory, self).triplify() + [
            (self._uri, RDF.type, STEP.RawTrajectory)
        ] + fix_tuples


class Fix(Resource):
    def __init__(self, point, instant):
        super(Fix, self).__init__()
        self.point = point
        self.instant = instant

    def __repr__(self):
        return '{{ "Fix": {{ {0}, {1}  }} }}'.format(self.point, self.instant)

    def triplify(self):
        return super(Fix, self).triplify() + [
            (self._uri, RDF.type, STEP.Fix),
            (self._uri, STEP.atTime, self.instant.uri),
            (self._uri, STEP.hasLocation, self.point.uri)
        ] + self.point.triplify() + self.instant.triplify()


class Point(SpatialExtent):
    def __init__(self, latitude, longitude, elevation=None):
        super(Point, self).__init__()
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.as_wkt = 'POINT({0} {1})'.format(latitude, longitude)

    def __repr__(self):
        return '"Point": {{ "lat": "{0}", "long": "{1}", "elev": "{2}"}}'.format(self.latitude, self.longitude, self.elevation)

    def triplify(self):
        return super(Point, self).triplify() + [
            (self._uri, RDF.type, SF.Point),
            (self._uri, GEO.asWKT, Literal(str(self.as_wkt), datatype=GEO.wktLiteral))
        ]
