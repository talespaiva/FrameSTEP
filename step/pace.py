import numpy as np
import pandas as pnd


def gap(interval_time, interval_distance, interval_grade):
    """
        interval_time in minutes
        interval_distance in kilometers
    """
    observed_pace = interval_time / interval_distance
    if interval_grade > 0:
        return incline_pace(interval_grade, observed_pace)
    else:
        return decline_pace(interval_grade, observed_pace)


def decline_pace(grade, observed_pace):
    coefficient_per_grade_point = 0.01815
    return observed_pace / (1 - (coefficient_per_grade_point * grade))


def incline_pace(grade, observed_pace):
    coefficient_per_grade_point = 0.033
    return observed_pace / (1 + (coefficient_per_grade_point * grade))


def graded_adjusted_pace(df):
    """
    Grade Adjusted Pace (GAP). Based on:

    https://github.com/andrewhao/stressfactor
    https://github.com/andrewhao/stressfactor/blob/master/lib/stressfactor/grade_adjusted_pace_strategy.rb
    http://www.runnersworld.com/races/downhill-all-the-way
    http://labs.strava.com/blog/improving-grade-adjusted-pace/

    :param df: a pandas dataframe with elevation, distance, time, and timestamp values
    :return: the graded adjusted pace
    """
    elevation_gain = np.array((np.ediff1d(df.elevation, to_begin=0)), dtype=float)
    grade = pnd.Series((elevation_gain/df.distance)*100, df.timestamp)

    time_min = df.time/60
    dist_km = df.distance/1000

    grade_adjusted_pace = [gap(t, d, g) for t, d, g in zip(time_min, dist_km, grade)]
    gap_series = pnd.Series(grade_adjusted_pace, df.timestamp)
    return gap_series.ewm(span=5).mean() #smoothed data

