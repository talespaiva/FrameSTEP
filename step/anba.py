import numpy as np
import pandas as pnd

from . import util


def anba(data, min_gvf=None, nclasses=0, min_dist=0.5, min_time=None):
    data_copy = np.copy(data.fillna(0))

    if min_gvf:
        gvf = 0.0
        nclasses = 1

        while gvf < min_gvf:
            gvf = goodness_of_variance_fit(data_copy, nclasses)
            nclasses += 1

        return anba(data, None, nclasses, min_dist, min_time)

    breaks = jenks(data_copy, nclasses)

    diffs = np.diff(breaks)
    groups = [[]] * nclasses

    for d in data:
        for i, (break_, diff) in enumerate(zip(breaks, diffs)):
            if d >= break_ and d < break_ + diff:
                groups[i] = np.append(groups[i], d)
                break

    medians = np.nan_to_num([np.median(x) for x in groups])
    merged_medians = merge_medians(medians, min_dist)

    newdata = snap_to_values(data, merged_medians, min_time)

    # reintroduce stops
    # TODO: this is specific for speed time series
    newdata[data[data == 0].index] = 0

    # reintroduce noise
    noise_indexes = [i for i, d in enumerate(data) if np.isnan(d)]
    newdata[noise_indexes] = None

    change_points = util.get_change_points(newdata)

    return newdata[change_points]


def merge_medians(medians, min_diff):
    merged_medians = medians

    medians_diff = np.ediff1d(medians, to_end=np.inf)
    mask = [True if d < min_diff else False for d in medians_diff]

    if any(mask):
        start = None
        end = None
        intervals = []
        for i, m in enumerate(mask):
            if m:
                if start is None:
                    start = i
            else:
                if start is not None:
                    end = i
                    intervals.append([start, end])
                    start = None

        newvalues = []
        oldvalues = []
        for interval in intervals:
            s = interval[0]  # start
            e = interval[1]  # end
            n = e - s + 1
            if n > 2:
                #newvalues.extend(list(np.arange(medians[s], medians[e], min_diff)))
                if (medians[e] - medians[s]) // min_diff >= 2:
                    print('>=2')
                    newvalues.extend(np.arange(medians[s], medians[e], min_diff))
                elif medians[e] - medians[s] > min_diff:
                    newvalues.extend([medians[s], medians[e]])
                else:
                    newvalues.extend([medians[s], medians[s] + min_diff])

                oldvalues.extend(medians[s:e + 1])
            elif n == 2:
                newvalues.extend([np.mean([medians[s], medians[e]])])
                oldvalues.extend(medians[s:e + 1])
            else:
                print("Merge medians warning")

        kept_medians = [x for x in medians if x not in oldvalues]
        merged_medians = np.sort(np.append(kept_medians, newvalues))

    return merged_medians


def snap_to_values(data, values, min_time):
    newdata = []

    for i, d in enumerate(data):
        absolute_distance = abs(d - values)
        bin_index = np.argmin(absolute_distance)
        newdata.append(values[bin_index])

    newdata = pnd.Series(newdata, index=data.index)

    # Adjust short segments to nearest possible neighbor
    # Considering only one point at a time
    if min_time:
        change_points = util.get_change_points(newdata)

        for i, (ch, d, date) in enumerate(zip(change_points, newdata[change_points], newdata.index[change_points])):
            if i == 0:
                continue

            prev_date = newdata.index[change_points[i - 1]]
            diff = ch - change_points[i - 1]
            time = (date - prev_date).seconds

            if diff <= 1 and time <= min_time and newdata[ch - 1] > 0.0 and newdata[ch - 1] != None:

                if i < 2:
                    left_neighbor = None
                    right_neighbor = newdata[ch]
                else:
                    left_neighbor = newdata[ch - 2]
                    right_neighbor = newdata[ch]

                if right_neighbor:
                    newdata[ch - 1] = right_neighbor
                else:
                    newdata[ch - 1] = left_neighbor

    return pnd.Series(newdata, index=data.index)


################################
### Goodness of Variance Fit ###
################################
def goodness_of_variance_fit(array, classes):
    # get the break points
    classes = jenks(array, classes)
    # do the actual classification
    classified = np.array([classify(i, classes) for i in array])
    # max value of zones
    maxz = max(classified)
    # nested list of zone indices
    zone_indices = [[idx for idx, val in enumerate(classified) if zone + 1 == val] for zone in range(maxz)]
    # sum of squared deviations from array mean
    sdam = np.sum((array - array.mean()) ** 2)
    # sorted polygon stats
    array_sort = [np.array([array[index] for index in zone]) for zone in zone_indices]
    # sum of squared deviations of class means
    sdcm = sum([np.sum((classified - classified.mean()) ** 2) for classified in array_sort])
    # goodness of variance fit
    gvf = (sdam - sdcm) / sdam

    return gvf


def classify(value, breaks):
    for i in range(1, len(breaks)):
        if value < breaks[i]:
            return i

    return len(breaks) - 1


############################
### Jenks Natural Breaks ###
############################
def jenks_matrices_init(data, n_classes):
    #fill the matrices with data+1 arrays of n_classes 0s
    lower_class_limits = []
    variance_combinations = []
    for i in range(0, len(data)+1):
        temp1 = []
        temp2 = []
        for j in range(0, n_classes+1):
            temp1.append(0.)
            temp2.append(0.)
        lower_class_limits.append(temp1)
        variance_combinations.append(temp2)

    inf = float('inf')
    for i in range(1, n_classes+1):
        lower_class_limits[1][i] = 1.
        variance_combinations[1][i] = 0.
        for j in range(2, len(data)+1):
            variance_combinations[j][i] = inf

    return lower_class_limits, variance_combinations


def jenks_matrices(data, n_classes):
    lower_class_limits, variance_combinations = jenks_matrices_init(data, n_classes)

    variance = 0.0
    for l in range(2, len(data)+1):
        sum = 0.0
        sum_squares = 0.0
        w = 0.0
        for m in range(1, l+1):
            # `III` originally
            lower_class_limit = l - m + 1
            val = data[lower_class_limit-1]

            # here we're estimating variance for each potential classing
            # of the data, for each potential number of classes. `w`
            # is the number of data points considered so far.
            w += 1

            # increase the current sum and sum-of-squares
            sum += val
            sum_squares += val * val

            # the variance at this point in the sequence is the difference
            # between the sum of squares and the total x 2, over the number
            # of samples.
            variance = sum_squares - (sum * sum) / w

            i4 = lower_class_limit - 1

            if i4 != 0:
                for j in range(2, n_classes+1):
                    if variance_combinations[l][j] >= (variance + variance_combinations[i4][j - 1]):
                        lower_class_limits[l][j] = lower_class_limit
                        variance_combinations[l][j] = variance + variance_combinations[i4][j - 1]

        lower_class_limits[l][1] = 1.
        variance_combinations[l][1] = variance

    return lower_class_limits, variance_combinations


def get_jenks_breaks(data, lower_class_limits, n_classes):
    k = len(data) - 1
    kclass = [0.] * (n_classes+1)
    countNum = n_classes

    kclass[n_classes] = data[len(data) - 1]
    kclass[0] = data[0]

    while countNum > 1:
        elt = int(lower_class_limits[k][countNum] - 2)
        kclass[countNum - 1] = data[elt]
        k = int(lower_class_limits[k][countNum] - 1)
        countNum -= 1

    return kclass


def jenks(data, n_classes):
    if n_classes > len(data): return
    data.sort()
    #data.sort_values(inplace=True)
    lower_class_limits, _ = jenks_matrices(data, n_classes)
    return get_jenks_breaks(data, lower_class_limits, n_classes)
