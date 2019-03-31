import numpy as np
import pandas as pnd
from step import msn


def paa(data, paa_size):
    data = np.array(data)
    if len(data) == paa_size:
        return data
    else:
        res = np.zeros(paa_size)
        for i in range(len(data) * paa_size - 1):
            idx = i // len(data)
            pos = i // paa_size
            res[idx] = res[idx] + data[pos]

        for i in range(paa_size):
            res[i] = res[i] / len(data)

        return res


def get_series(data, paa_size):
    paa_data = paa(data, paa_size)

    paa_segments = []
    for i, v in enumerate(paa_data):
        if i < len(paa_data) - 1:
            paa_segments.append([i, v, i + 1, v])

    paa_size = int(len(data) / paa_size)
    new_paa = np.array([[x] * paa_size for x in paa_data]).flatten()

    if len(new_paa) < len(data):
        missing_len = len(data) - len(new_paa)
        last_points = [paa_data[-1]] * missing_len
        new_paa = np.append(new_paa, last_points)

    return pnd.Series(new_paa, index=data.index)
