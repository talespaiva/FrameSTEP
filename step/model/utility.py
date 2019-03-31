from . import step


def create_raw_trajectory(gpx):
    raw = step.RawTrajectory()
    fixes_array = []
    points = gpx.get_points_data()
    for point_data in points:
        point = point_data.point

        step_point = step.Point(point.latitude, point.longitude, point.elevation)
        step_time = step.TimeInstant(point.time)

        fixes_array.append(step.Fix(step_point, step_time))

    raw.fixes = fixes_array
    return raw


def series_to_foi(foi_label, series, gpx):
    """
    Creates a Feature of Intestes from a time series
    :param foi_label: Feature of Interest label
    :param series: the time series as a Pandas Series
    :param gpx: A gpx object from gpxpy
    :return: a STEP FeatureOfInterest object
    """
    foi = step.FeatureOfInterest(foi_label)

    raw = create_raw_trajectory(gpx)

    for point1, idx1, point2, idx2 in zip(series, series.index, series[1:], series.index[1:]):
        fix1 = raw.get_fix(idx1)
        fix2 = raw.get_fix(idx2)
        st_extent = step.SpatiotemporalExtent(fix1, fix2)
        quant_value = step.QuantitativeValue(point1, 'min/km')
        episode = step.Episode(st_extent, quant_value)
        foi.add_episode(episode)

    return foi


def foi_to_series(foi):
    """
    Transforms a FoI into a Pandas time series
    :param foi: A STEP FeatureOfInterest
    :return: a pandas Series
    """
    value = []
    index = []
    #TODO
    pass