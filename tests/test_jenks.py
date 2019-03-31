import numpy as np

from step import msn
from step import anba
from tests import util


def test_jenks_1():
    df = util.get_dataframe(r'data/1583713025.gpx')
    #moves, stops, noise = msn.get_move_stop_noise(df)

    noise_indexes = msn.get_noise(df)
    df2 = df.drop(df.index[noise_indexes])
    stop_indexes = msn.get_stops(df2)

    data = df.speed
    data = data.ewm(span=5).mean()  # smoothed data
    data[stop_indexes] = 0  ########################

    min_gvf = .6
    newdata = anba.anba(data, min_gvf=min_gvf)
    print(newdata.as_matrix())

    #expected_breaks = [0.0, 1.5913603760880239, 2.2769534045274042]

    #np.testing.assert_array_equal(breaks, expected_breaks)
