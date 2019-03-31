import numpy as np
import pandas as pnd
from .paa import paa
from step import util


def create_series(segments, data):
    pls = []
    for seg in segments:
        length = seg[2] - seg[0]
        #interpolated = np.linspace(seg[1], seg[3], length)
        median = data.iloc[seg[0]:seg[2]].median()
        interpolated = np.linspace(median, median, length)
        pls.extend(interpolated)

    if len(pls) < len(data):
        points_left = len(data) - len(pls)
        pls.extend(data[len(data) - points_left:])
        #print('WARNING: create_series - original points appended:', points_left)

    pls = pnd.Series(pls, index=data.index)

    # reintroduce stops
    pls[data[data == 0].index] = 0

    #reintroduce noise
    noise_indexes = [i for i, d in enumerate(data) if np.isnan(d)]
    pls[noise_indexes] = None

    return pls


def call(func, data, fit_type, error_type, max_error):
    segments = func(data, fit_type, error_type, max_error)

    new_segments = []
    for s in segments:
        mean = np.mean([s[1], s[3]])
        new_segments.append([s[0], mean, s[2], mean])

    series = create_series(new_segments, data)
    change_points = util.get_change_points(series)

    return series[change_points]


def call_paa(data, paa_size):
    paa_data = paa(data, paa_size)

    paa_segments = []
    for i, v in enumerate(paa_data):
        if i < len(paa_data) - 1:
            paa_segments.append([i, v, i + 1, v])

    segment_length = int(len(data) / paa_size)
    new_paa = np.array([[x] * segment_length for x in paa_data]).flatten()

    if len(new_paa) < len(data):
        missing_len = len(data) - len(new_paa)
        last_points = [paa_data[-1]] * missing_len
        new_paa = np.append(new_paa, last_points)

    paa_series  = pnd.Series(new_paa, index=data.index)

    # reintroduce stops
    paa_series[data[data == 0].index] = 0

    # reintroduce noise
    noise_indexes = [i for i, d in enumerate(data) if np.isnan(d)]
    paa_series[noise_indexes] = None

    change_points = util.get_change_points(new_paa)

    return pnd.Series(new_paa[change_points], index=data.index[change_points])
