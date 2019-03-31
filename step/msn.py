import pandas as pnd
import numpy as np

from . import preprocessing, util
from . import stats as st


def get_move_stop_noise(df, distance_threshold=3.5, direction_threshold=45, speed_threshold=3.5,
                        time_threshold=5, jitter=0.01):

    noise = get_noise(df)

    df_clean = df.drop(df.index[noise])
    stops = get_stops(df_clean, jitter)

    moves = get_moves(df, noise, stops)

    moves = util.get_interval_limits(moves, tolerance=0)
    stops = util.get_interval_limits(stops)
    noise = util.get_interval_limits(noise)
    
    return moves, stops, noise


# Noise
def get_noise(df, distance_threshold=3.5, direction_threshold=45):
    distance_outliers_indexes = distance_outliers(df, distance_threshold)
    direction_outliers_indexes = direction_outliers(df, direction_threshold)

    all_noise_indexes = np.array([])
    all_noise_indexes = np.concatenate((all_noise_indexes, distance_outliers_indexes))
    all_noise_indexes = np.concatenate((all_noise_indexes, direction_outliers_indexes))
    all_noise_indexes = np.sort(all_noise_indexes)

    # get isolated points between two noisy points
    intervals = util.get_interval_limits(all_noise_indexes)

    all_noise_indexes = np.array([])
    for interval in intervals:
        linspace = np.linspace(interval[0], interval[1], interval[1] - interval[0] + 1)
        all_noise_indexes = np.concatenate((all_noise_indexes, linspace))

    return np.array(np.sort(all_noise_indexes), dtype=int)


def distance_outliers(df, distance_threshold=3.5):
    mz_dist = st.modified_zscore(df['distance'])
    long_distances_i = [i for i, mz in enumerate(mz_dist) if mz > distance_threshold]

    return long_distances_i


def direction_outliers(df, min_direction_threshold=45, max_sequential_sharp_angles=1):
    sharp_angles = df[df['angle'] < min_direction_threshold][0:-1]
    # [0:-1] because the last angle is always equals to zero (get_movement_parameters)

    sharp_angles_i = [df.index.get_loc(i) for i in sharp_angles.index]

    diff = np.ediff1d(sharp_angles_i, np.inf)
    mask = [True if d <= max_sequential_sharp_angles + 1 else False for d in diff]

    direction_outliers = []
    for i, m in enumerate(mask):
        if m:
            direction_outliers.append(sharp_angles_i[i])
            direction_outliers.append(sharp_angles_i[i + 1])

    direction_intervals = util.get_interval_limits(direction_outliers)

    direction_i = []
    for interval in direction_intervals:
        direction_i.extend(
            np.linspace(interval[0], interval[1], interval[1] - interval[0] + 1, dtype=int))

    return direction_i


# Stop
def get_stops(df, speed_threshold=3.5, time_threshold=5, jitter=.01):
    # Time
    j_time = preprocessing.jitter(df['duration'], jitter)
    mz_time = st.modified_zscore(j_time)
    long_time_indexes = [i for i, mz in enumerate(mz_time) if mz > time_threshold]
    long_time_indexes = df.iloc[long_time_indexes]['idx'].values
    q = 'idx in {}'.format(list(long_time_indexes))
    long_time_indexes = df.query(q)['idx'].values

    # Speed
    log_speed = np.log(df['speed'])
    mz_speed = st.modified_zscore(log_speed)
    slowest_speed_indexes = [i for i, mz in enumerate(mz_speed) if mz < -speed_threshold]
    slowest_speed_indexes = df.iloc[slowest_speed_indexes]['idx'].values
    q = 'idx in {}'.format(list(slowest_speed_indexes))
    slowest_speed_indexes = df.query(q)['idx'].values

    # Intersection
    return np.intersect1d(long_time_indexes, slowest_speed_indexes)


# Move
def get_moves(df, noise_i, stops_i):
    moves_i = np.linspace(0, len(df) - 1, len(df), dtype=int)

    non_move_i = np.array([])
    non_move_i = np.concatenate((non_move_i, noise_i))
    non_move_i = np.concatenate((non_move_i, stops_i))

    moves_i = np.delete(moves_i, non_move_i)

    return moves_i

