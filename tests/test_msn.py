from step import msn
from tests import util

import numpy as np


def test_msn_1():
    expected_noise = [[27, 28], [66, 66]]
    expected_stops = [[14, 14], [44, 44]]
    expected_moves = [[0, 13], [15, 26], [29, 43], [45, 65], [67, 73]]

    df = util.get_dataframe(r'data/1583713025.gpx')
    moves, stops, noise = msn.get_move_stop_noise(df)

    np.testing.assert_array_equal(moves, expected_moves)
    np.testing.assert_array_equal(stops, expected_stops)
    np.testing.assert_array_equal(noise, expected_noise)


def test_msn_2():
    expected_noise = [[34, 34], [437, 437], [442, 445], [572, 572], [606, 607]]
    expected_stops = [[352, 352], [630, 630], [769, 769]]
    expected_moves = [[0, 33], [35, 351], [353, 436], [438, 441], [446, 571], [573, 605], [608, 629], [631, 768], [770, 801]]

    df = util.get_dataframe(r'data/1100430165.gpx')
    moves, stops, noise = msn.get_move_stop_noise(df)

    np.testing.assert_array_equal(moves, expected_moves)
    np.testing.assert_array_equal(stops, expected_stops)
    np.testing.assert_array_equal(noise, expected_noise)


def test_msn_3():
    expected_noise = []
    expected_stops = [[163, 163], [268, 268]]
    expected_moves = [[0, 162], [164, 267], [269, 341]]

    df = util.get_dataframe(r'data/995057635.gpx')
    moves, stops, noise = msn.get_move_stop_noise(df)

    np.testing.assert_array_equal(moves, expected_moves)
    np.testing.assert_array_equal(stops, expected_stops)
    np.testing.assert_array_equal(noise, expected_noise)

def test_msn_4():
    expected_noise = [[89, 89], [191, 191]]
    expected_stops = [[113, 113], [118, 118], [140, 140], [171, 173], [192, 192], [202, 202],
                      [241, 241], [248, 248], [251, 251]]
    expected_moves = [[0, 88], [90, 112], [114, 117], [119, 139], [141, 170], [174, 190],
                      [193, 201], [203, 240], [242, 247], [249, 250], [252, 252]]

    df = util.get_dataframe(r'data/950590555.gpx')
    moves, stops, noise = msn.get_move_stop_noise(df)

    np.testing.assert_array_equal(moves, expected_moves)
    np.testing.assert_array_equal(stops, expected_stops)
    np.testing.assert_array_equal(noise, expected_noise)

def test_msn_5():
    expected_noise = [[0, 6], [9, 10], [77, 78], [155, 155], [189, 191], [269, 269], [376, 378]]
    expected_stops = [[53, 53], [79, 79], [94, 94], [143, 143], [147, 147], [150, 152], [156, 156],
                      [163, 163], [174, 174], [178, 178], [182, 185], [188, 188]]
    expected_moves = [[7, 8], [11, 52], [54, 76], [80, 93], [95, 142], [144, 146], [148, 149],
                      [153, 154], [157, 162], [164, 173], [175, 177], [179, 181], [184, 184],
                      [186, 187], [192, 268], [270, 375], [379, 565]]

    df = util.get_dataframe(r'data/709085461.gpx')
    moves, stops, noise = msn.get_move_stop_noise(df)

    np.testing.assert_array_equal(moves, expected_moves)
    np.testing.assert_array_equal(stops, expected_stops)
    np.testing.assert_array_equal(noise, expected_noise)

