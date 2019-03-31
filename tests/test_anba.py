import numpy as np

from step import anba

def test_merge_medians_no_merge():
    min_diff = 1
    input = np.array([1, 3, 5])
    expected = np.array([1, 3, 5])
    output = anba.merge_medians(input, min_diff)
    np.testing.assert_array_equal(output, expected)


def test_merge_medians_1_merge():
    min_diff = 0.5
    input = np.array([2, 2.4, 3, 3.5])
    expected = np.array([2.2, 3, 3.5])
    output = anba.merge_medians(input, min_diff)
    np.testing.assert_array_equal(output, expected)


def test_merge_medians_2_merges():
    min_diff = 0.5
    input = np.array([2, 2.4, 2.7, 3.5])
    expected = np.array([2, 2.7, 3.5])
    output = anba.merge_medians(input, min_diff)
    np.testing.assert_array_equal(output, expected)


def test_merge_medians_3_merges():
    min_diff = 0.5
    input = np.array([2, 2.4, 2.7, 3, 3.3, 5])
    expected = np.array([2, 2.5, 3, 5])
    output = anba.merge_medians(input, min_diff)
    np.testing.assert_array_equal(output, expected)
