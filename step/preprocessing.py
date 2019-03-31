import math
import numpy as np
import srtm
import pandas as pnd


def discard(gpx, timedelta):
    # formely ignore_fist)

    new_gpx = gpx.clone()
    to_remove = []

    first_point = gpx.get_points_data()[0].point

    for track in new_gpx.tracks:
        for segment in track.segments:
            for i, point in enumerate(segment.points):
                time_difference = first_point.time_difference(point)
                if time_difference < timedelta.seconds:
                    to_remove.append(i)

    for track in new_gpx.tracks:
        for segment in track.segments:
            segment.points = [i for j, i in enumerate(segment.points) if j not in to_remove]

    return new_gpx


def get_turning_angle(p1, p2, p3):
    distance_p1p2 = p1.distance_2d(p2)
    distance_p2p3 = p2.distance_2d(p3)
    distance_p1p3 = p1.distance_2d(p3)

    if distance_p1p3 == 0 or distance_p1p2 == 0 or distance_p2p3 == 0:
        angle = 180
    else:
        # angle having p2 as vertex:
        try:
            angle = math.acos((distance_p1p2 ** 2 + distance_p2p3 ** 2 - distance_p1p3 ** 2) / (
                2 * distance_p1p2 * distance_p2p3))

            angle = math.degrees(angle)
        except ValueError:  # when there's no angle to calculate (near 180 degrees)
            angle = 180

    return angle


def get_heading(p1, p2):
    # https://gist.github.com/jeromer/2005586
    lat1 = math.radians(p1.latitude)
    lat2 = math.radians(p2.latitude)

    diff_long = math.radians(p2.longitude - p1.longitude)

    x = math.sin(diff_long) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diff_long))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return round(compass_bearing)


def get_acceleration(previous_point, current_point, next_point):
    initial_speed = previous_point.speed_between(current_point)
    current_speed = current_point.speed_between(next_point)
    time = current_point.time_difference(next_point)

    acc = 0
    if initial_speed and current_speed and time:
        acc = (current_speed - initial_speed) / time

    return acc


def filter_points(gpx):
    """
    Remove points recorded at the same time
    :param gpx: a gpxpy GPX object
    :return: a new gpx without points captured at the same time (only the last one is kept)
    """
    new_gpx = gpx.clone()
    to_remove = []

    for track in new_gpx.tracks:
        for segment in track.segments:
            for i, point in enumerate(segment.points):
                if i < len(segment.points)-1:
                    next_point = segment.points[i+1]
                    time_difference = point.time_difference(next_point)
                    if time_difference == 0:
                        to_remove.append(i)

    for track in new_gpx.tracks:
        for segment in track.segments:
                segment.points = [i for j, i in enumerate(segment.points) if j not in to_remove]

    return new_gpx


def get_movement_attributes(gpx):
    gpx = filter_points(gpx)

    angle = []
    acceleration = []
    distance = []
    duration = []
    timestamp = []
    speed = []
    heading = []
    latitude = []
    longitude = []
    elevation = []

    try:
        elevation_data = srtm.get_data()
        elevation_data.add_elevations(gpx, smooth=True)
    except:
        pass

    points = gpx.get_points_data()

    for i, point_data in enumerate(points):
        point = point_data.point

        pairwise_distance = 0
        pairwise_duration = 0
        turning_angle = 0
        acc = 0
        spd = 0
        head = 0

        if i > 0:
            previous_point_data = points[i-1]

            pairwise_distance = point_data.distance_from_start - previous_point_data.distance_from_start
            pairwise_duration = previous_point_data.point.time_difference(point)
            spd = previous_point_data.point.speed_between(point)
            head = get_heading(previous_point_data.point, point)

        if len(points)-1 > i > 0:
            previous_point = points[i-1].point
            next_point = points[i+1].point

            turning_angle = get_turning_angle(previous_point, point, next_point)
            acc = get_acceleration(previous_point, point, next_point)

        elev = point.elevation or 0

        timestamp.append(point.time)
        distance.append(np.around(pairwise_distance, 2))
        duration.append(pairwise_duration)
        angle.append(np.around(turning_angle, 2))
        acceleration.append(np.around(acc, 2))
        speed.append(np.around(spd, 2))
        heading.append(head)
        latitude.append(point.latitude)
        longitude.append(point.longitude)
        elevation.append(round(elev))

    return {'distance': distance,
            'duration': duration,
            'angle': angle,
            'acceleration': acceleration,
            'speed': speed,
            'heading': heading,
            'latitude': latitude,
            'longitude': longitude,
            'elevation': elevation,
            'timestamp': timestamp}


def compute_attributes(gpx):
    movement_attributes = get_movement_attributes(gpx)
    colums = ['latitude', 'longitude', 'distance',
              'duration', 'speed', 'acceleration', 'heading',
              'angle', 'elevation', 'timestamp']
    df_all = pnd.DataFrame(movement_attributes, index=movement_attributes['timestamp'], columns=colums)
    df = df_all[1:]
    i_series = pnd.Series(np.arange(len(df)), index=df.index).rename('idx')
    df = pnd.concat([df, i_series], axis=1)

    return df

def jitter(x, amount):
    return x + np.random.uniform(-amount, amount, len(x))