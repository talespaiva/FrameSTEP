from datetime import timedelta
import pandas as pnd
import numpy as np
import os

import gpxpy

from step import preprocessing


def get_dataframe(gpx_path):
    gpx = gpxpy.parse(open(os.path.join(os.path.dirname(__file__), gpx_path)))
    # Ignore first 30 seconds (to avoid GPS "time to first fix")
    gpx = preprocessing.discard(gpx, timedelta(seconds=30))

    movement_attributes = preprocessing.get_movement_attributes(gpx)
    df_all = pnd.DataFrame(movement_attributes, index=movement_attributes['timestamp'])

    df = df_all[1:]  # in df_all[0], all values equals to 0, therefore [1:] is returned
    i_series = pnd.Series(np.arange(len(df)), index=df.index).rename('idx')
    df = pnd.concat([df, i_series], axis=1)

    return df
