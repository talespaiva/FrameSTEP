import pandas as pnd
import overpy
from shapely import wkt
from shapely.geometry import LineString
from shapely.ops import polygonize_full, cascaded_union


def get_spatial_features(gpx, keys):
    gpx_simple = gpx.clone()
    gpx_simple.simplify()

    linestring_simple = "LINESTRING("

    points_data = gpx_simple.get_points_data()

    for i, point_data in enumerate(points_data):
        point = point_data.point
        linestring_simple += str(point.longitude) + " " + str(point.latitude)
        if i < len(points_data)-1:
            linestring_simple += ", "

    linestring_simple += ")"

    # Query with Overpass API
    simplified_trajectory = wkt.loads(linestring_simple)
    overpass_polygon = ""
    for coord in simplified_trajectory.coords:
        overpass_polygon += str(coord[1]) + " " + str(coord[0]) + " "

    if overpass_polygon[-1] == ' ':  # trim
        overpass_polygon = overpass_polygon[:-1]

    #keys = ["leisure", "waterway", "natural"]  # , "surface"]
    if len(keys) > 0:
        keys_regex = "|".join(keys)
    else:
        keys_regex = "."

    tag_regex = """[~"{0}"~"."]""".format(keys_regex)

    overpass_query = """
        [out:json];
        (way{0}
        (poly:"{1}");
        rel(bw);

        relation{0}
        (poly:"{1}"););
        out geom;
        """.format(tag_regex, overpass_polygon)

    #print(overpass_query)

    api = overpy.Overpass()
    result = api.query(overpass_query)

    response = []
    keys_to_keep = keys + ['name']

    for relation in result.relations:
        new_dict = {}

        # subject
        new_dict.update({'id': relation.id})

        # relation
        new_dict.update({'relation': None})

        # tags
        tags = {}
        for key, value in relation.tags.items():
            #if key in keys_to_keep:
                tags.update({key: value})
        new_dict.update({'tags': tags})

        # label
        label = None
        if 'name' in relation.tags:
            label = relation.tags['name']

        new_dict.update({'label': label})

        # geometry
        relation_geometry = "MULTILINESTRING("
        for i, member in enumerate(relation.members):
            if type(member) == overpy.RelationWay:
                member_geometry = "("
                for j, point in enumerate(member.geometry):
                    member_geometry += str(point.lon) + " " + str(point.lat)
                    if j < len(member.geometry) - 1:
                        member_geometry += ","

                member_geometry += ")"

                if i < len(relation.members) - 1:
                    member_geometry += ","

                relation_geometry += member_geometry

        relation_geometry += ')'
        new_dict.update({'geometry': relation_geometry})

        response.append(new_dict)

    for way in result.ways:
        new_dict = {}

        # subject
        new_dict.update({'id': way.id})

        part_of = []
        for relation in result.relations:
            if way.id in [member.ref for member in relation.members]:
                part_of.append(relation.id)
        new_dict.update({'relation': part_of})

        # tags
        # tags
        tags = {}
        for key, value in way.tags.items():
            #if key in keys_to_keep:
                tags.update({key: value})
        new_dict.update({'tags': tags})

        # label
        label = None
        if 'name' in way.tags:
            label = way.tags['name']

        new_dict.update({'label': label})

        # geometry
        linestring = 'LINESTRING('
        for i, point in enumerate(way.attributes['geometry']):
            linestring += str(point['lon']) + " " + str(point['lat'])
            if i < len(way.attributes['geometry']) - 1:
                linestring += ", "

        linestring += ')'
        new_dict.update({'geometry': linestring})

        response.append(new_dict)

    df = pnd.DataFrame(response)
    if len(df) > 0:
        df = df.set_index('id')

    return df


def compute_intersections(gpx, osm_data, buffer_size=0.0002):
    # buffer_size = 0.0002  # ~20 meters

    points_data = gpx.get_points_data()
    linestring = "LINESTRING("
    for i, point_data in enumerate(points_data):
        point = point_data.point
        linestring += str(point.longitude) + " " + str(point.latitude)
        if i < len(points_data) - 1:
            linestring += ", "

    linestring += ")"
    trajectory = wkt.loads(linestring)

    # create polygons to be considered for intersections
    features = []
    for item in osm_data.itertuples():
        try:
            feature = wkt.loads(item.geometry)
            buffered_feature = feature.buffer(buffer_size)
            feature = polygonize_full(feature)[0]
            feature = cascaded_union([buffered_feature, feature])
            features.append(feature)
        except Exception as e:
            print(e, item.tags)
            print(item.Index)
            features.append(LineString())
            continue

    intersections = [trajectory.intersection(feat) for feat in features]

    trajectory_total_length = gpx.length_3d()
    trajectory_total_duration = gpx.get_duration()
    feature_intervals = []
    for i in range(len(intersections)):
        intervals = []
        try:
            iter(intersections[i])
        except TypeError:
            # to avoid "TypeError: 'LineString' object is not iterable", we make it always iterable:
            intersections[i] = [intersections[i]]

        for geometry in intersections[i]:
            trajectory_indexes = [j for j, p in enumerate(trajectory.coords) if p in geometry.coords]
            if len(trajectory_indexes) > 0:
                intervals.append([trajectory_indexes[0], trajectory_indexes[-1]])

        # merge neighbor intervals
        gap = 3
        opened = False
        new_intervals = []
        for interval, next_interval in zip(intervals, intervals[1:] + [[0, 0]]):
            if abs(next_interval[0] - interval[1]) <= gap:
                if not opened:
                    opened = True
                    start = interval[0]
            elif opened:
                opened = False
                end = interval[1]
                new_intervals.append([start, end])
            else:
                new_intervals.append(interval)
        #

        for new_interval in new_intervals:
            start_point_data = points_data[new_interval[0]]
            end_point_data = points_data[new_interval[1]]
            interval_length = end_point_data.distance_from_start - start_point_data.distance_from_start
            interval_duration = (end_point_data.point.time - start_point_data.point.time).total_seconds()

            interval_info = {
                'id': osm_data.index[i],
                'start_index': new_interval[0],
                'end_index': new_interval[1],
                'interval_length': interval_length,
                'interval_duration': interval_duration,
                'duration_ratio': interval_duration/trajectory_total_duration,
                'length_ratio': interval_length/trajectory_total_length,
            }

            feature_intervals.append(interval_info)

    df = pnd.DataFrame(feature_intervals)
    if len(df) > 0:
        df = df.set_index('id')

    return df
