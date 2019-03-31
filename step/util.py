import numpy as np


def get_interval_limits(array, tolerance=1):
    diff = np.ediff1d(array, np.inf)
    mask = [True if d <= abs(tolerance+1) else False for d in diff]
    # d <= 2 includes 'normal' observations between 2 'abnormal' observations

    start = None
    intervals = []
    for i in range(len(array)):
        if mask[i]:
            if start is None:
                start = array[i]
                continue
        else:
            end = array[i]
            if start is None:
                start = array[i]

            intervals.append([start, end])
            start, end = None, None

    return intervals


def get_change_points(array):
    change_points = [0]

    for i, (d1, d2) in enumerate(zip(array, array[1:])):
        if d1 != d2 and not(np.isnan(d1) and np.isnan(d2)):
                change_points.extend([i+1])

    change_points.append(len(array)-1)

    return np.unique(np.array(change_points))


def get_no_segments(array):
    """
    Return number of segments
    :param array:
    :return: number of segments
    """
    seg = len(get_change_points(array)) - 1
    if seg < 1:
        raise Exception("Number of segments less than 1.")

    return seg
