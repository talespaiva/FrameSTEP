import numpy as np

from step import stats


def test_mad():
    measurements1 = [6.27, 6.34, 6.25, 63.1, 6.28]
    measurements2 = [6.27, 6.34, 6.25, 6.31, 6.28]

    result1 = stats.mad(measurements1)
    result2 = stats.mad(measurements2)
    expected = [0.044]

    np.testing.assert_almost_equal(result1, expected, decimal=2)
    np.testing.assert_almost_equal(result2, expected, decimal=2)


def test_modified_zscore():
    measurements = [6.27, 6.34, 6.25, 63.1, 6.28]
    result = stats.modified_zscore(measurements)

    #expected = np.array([-0.225, 1.35, -0.674, 1277.14, 0.0])
    expected = np.array([-0.151, 0.91, -0.454, 861.43, 0.0])
    print(result)

    for r, e in zip(result, expected):
        np.testing.assert_almost_equal(r, e, decimal=2)


def test_double_mad():
    measurements = [1, 4, 4, 4, 5, 5, 5, 5, 7, 7, 8, 10, 16, 30]
    result = stats.double_mads_from_median(measurements)
    result = [r for r in result if r > 3]

    expected = np.array([1, 16 , 30])

    for r, e in zip(result, expected):
        np.testing.assert_array_equal(r, e)
