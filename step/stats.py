import numpy as np
import statsmodels.api as sm
import pandas as pnd

from mpl_toolkits.mplot3d import Axes3D


def mad(x):
    return 1.483 * np.median(np.abs(x - np.median(x)))


def modified_zscore(x):
    return 0.6745 * (x - np.median(x)) / mad(x)


def mmz(x):
    return max(modified_zscore(x))


# http://eurekastatistics.com/using-the-median-absolute-deviation-to-find-outliers/
def double_mad(x):
    pass


def double_mads_from_median(x):
    pass


def standard_boxplot(series):
    q1, q3 = np.percentile(series, [25, 75])
    iqr = q3 - q1
    w1, w2 = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return w1, w2


def adjusted_boxplot(series):
    q1, q3 = np.percentile(series, [25, 75])
    mc = sm.stats.stattools.medcouple(series)
    iqr = q3 - q1

    if mc > 0:
        w1 = q1 - (1.5 * np.e ** (-4 * mc) * iqr)
        w2 = q3 + (1.5 * np.e ** (3 * mc) * iqr)
    else:
        w1 = q1 - (1.5 * np.e ** (-3 * mc) * iqr)
        w2 = q3 + (1.5 * np.e ** (4 * mc) * iqr)

    return w1, w2


def stahel_donoho_outlyingness(series):
    med = np.median(series)
    return abs(series - med) / mad(series)


def adjusted_outlyingness(series):
    _ao = []

    med = np.median(series)
    w1, w2 = adjusted_boxplot(series)

    for s in series:
        if s > med:
            _ao.append((s - med) / (w2 - med))
        else:
            _ao.append((med - s) / (med - w1))

    return pnd.Series(_ao, index=series.index)


# Outlier labeling rule
# Turkey, 1977:
# g = 1.5 or 3

# Hoaglin, 1987:
# g = 2.2

# Carey et al. (1997):
# formulas for g with n = 2000

# Kimber (1990):
# M = median
def label_outliers(series, g, method='turkey'):
    # compute quartiles
    q1, q3 = np.percentile(series, [25, 75])

    if method == 'turkey':
        lower_bound = q1 - g * (q3 - q1)
        upper_bound = q3 + g * (q3 - q1)

    if method == 'kimber':
        median = np.median(series)
        lower_bound = q1 - g * (median - q1)
        upper_bound = q3 + g * (q3 - median)

    return lower_bound, upper_bound


def mahalanobis(x, y, V):
    return np.sqrt((x - y).transpose() * V.I * (x - y).reshape(len(x), 1))

