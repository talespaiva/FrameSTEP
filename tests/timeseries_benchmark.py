import logging
import numpy as np
import pandas as pnd
import gpxpy
import time
import traceback
from datetime import timedelta

from simplesegment import segment, fit

from step import preprocessing as pp
from timeseries import benchmark as bm
from step.anba import anba
from step import msn, util

import matplotlib.pyplot as plt

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
log.addHandler(log_handler)


def measure_time(repeat, func, *args, **kwargs):
    all_runs = []
    for _ in range(repeat):
        start_time = time.perf_counter()
        func(*args, **kwargs)
        run_time = time.perf_counter() - start_time

        all_runs.append(run_time)

    return min(all_runs)


if __name__ == '__main__':

    def update_metrics(key, rmse, correlation, run_time, seg):
        metrics.loc[key].rmse = rmse
        metrics.loc[key].correlation = correlation
        metrics.loc[key].time = run_time
        metrics.loc[key].segments = seg


    log.info("Starting benchmark")
    trajectories = pnd.DataFrame.from_csv(r"C:\Users\Tales\Documents\MEGAsync\Thesis\src\STAT\run_grenoble.csv")

    df_dict = {}
    limit = None
    i = 1

    for trajectory in trajectories.itertuples():
        log.info(i)
        log.info(trajectory.path)

        if trajectory.n_points > 400:
            log.info('skipping long trajectory')
            continue

        path = trajectory.path
        #path = r'C:\DATA\MapMyRun\Grenoble\27031614\16_16_Run _ Jog\1459349483.gpx'

        try:
            gpx = gpxpy.parse(open(path, 'r'))
            # Ignore first 30 seconds (to avoid GPS "time to first fix")
            gpx = pp.discard(gpx, timedelta(seconds=30))


            mov_attr = pp.get_movement_attributes(gpx)
            df_all = pnd.DataFrame(mov_attr, index=mov_attr['timestamp'])

            df = df_all[1:]
            i_series = pnd.Series(np.arange(len(df)), index=df.index).rename('idx')
            df = pnd.concat([df, i_series], axis=1)

            #moves, stops, noise = msn.get_move_stop_noise(df)
            noise_indexes = msn.get_noise(df)

            df2 = df.drop(df.index[noise_indexes])
            stop_indexes = msn.get_stops(df2)

            speed = df.speed[:]
            speed[noise_indexes] = None
            speed[stop_indexes] = 0

            series = speed[:]
            data = series.ewm(span=5).mean()  # smoothed data
            data[noise_indexes] = None
            data[stop_indexes] = 0

            data_copy = data[:]
            data_copy = data_copy.fillna(0)

            # how many runs for each call
            repeat = 3

            keys = ['anba-n', 'anba-gvf', 'paa', 'swr', 'swi', 'bur', 'bui', 'tdr', 'tdi']
            columns = ['rmse', 'correlation', 'time', 'segments']
            metrics = pnd.DataFrame(index=keys, columns=columns)

            # ANBA
            min_dist = 1
            min_time = np.percentile(df.time, 90)

            # ANBA N
            log.info('ANBA n')
            nclasses = 3

            anba_data_n = anba(data, None, nclasses, min_dist, min_time)

            run_time = measure_time(repeat, anba, data, None, nclasses, min_dist, min_time)
            rmse = np.sqrt(((anba_data_n - data) ** 2).mean())
            correlation = anba_data_n.corr(data)

            seg = util.get_no_segments(anba_data_n)

            update_metrics('anba-n', rmse, correlation, run_time, seg)

            # ANBA GVF
            log.info('ANBA GVF')
            min_gvf = 0.5

            anba_data_gvf = anba(data, min_gvf, None, min_dist, min_time)
            run_time = measure_time(repeat, anba, data, min_gvf, None, min_dist, min_time)
            rmse = np.sqrt(((anba_data_gvf - data) ** 2).mean())
            correlation = anba_data_gvf.corr(data)

            seg = util.get_no_segments(anba_data_gvf)

            update_metrics('anba-gvf', rmse, correlation, run_time, seg)

            # PAA
            log.info('PAA')
            paa_size = sum(df.time) // 60  # split each 60 seconds
            paa_index = data.index[::paa_size]
            paa_size = len(paa_index)

            paa_data = bm.call_paa(data, paa_size)

            run_time = measure_time(repeat, bm.call_paa, data, paa_size)
            rmse = np.sqrt(((paa_data - data) ** 2).mean())
            correlation = paa_data.corr(data)
            seg = util.get_no_segments(paa_data)

            update_metrics('paa', rmse, correlation, run_time, seg)

            #PLS
            max_error = 1

            # Sliding Window with Interpolation
            log.info("Sliding Window with Interpolation")
            pls_data = bm.call(segment.slidingwindowsegment, data_copy, fit.interpolate, fit.sumsquared_error_int, max_error)

            run_time = measure_time(repeat, bm.call, segment.slidingwindowsegment, data_copy, fit.interpolate, fit.sumsquared_error_int, max_error)
            rmse = np.sqrt(((pls_data - data) ** 2).mean())
            correlation = pls_data.corr(data)
            seg = util.get_no_segments(pls_data)

            update_metrics('swi', rmse, correlation, run_time, seg)

            # Sliding Window with Regression
            log.info("Sliding Window with Regression")
            pls_data = bm.call(segment.slidingwindowsegment, data_copy, fit.regression, fit.sumsquared_error_regr, max_error)

            run_time = measure_time(repeat, bm.call, segment.slidingwindowsegment, data_copy, fit.regression, fit.sumsquared_error_regr, max_error)
            rmse = np.sqrt(((pls_data - data) ** 2).mean())
            correlation = pls_data.corr(data)
            seg = util.get_no_segments(pls_data)

            update_metrics('swr', rmse, correlation, run_time, seg)

            # Bottom-up with Interpolation
            log.info("Bottom-up with Interpolation")
            pls_data = bm.call(segment.bottomupsegment, data_copy, fit.interpolate, fit.sumsquared_error_int, max_error)

            run_time = measure_time(repeat, bm.call, segment.bottomupsegment, data_copy, fit.interpolate, fit.sumsquared_error_int, max_error)
            rmse = np.sqrt(((pls_data - data) ** 2).mean())
            correlation = pls_data.corr(data)
            seg = util.get_no_segments(pls_data)

            update_metrics('bui', rmse, correlation, run_time, seg)

            # Bottom-up with Regression
            log.info("Bottom-up with Regression")
            pls_data = bm.call(segment.bottomupsegment, data_copy, fit.regression, fit.sumsquared_error_regr, max_error)

            run_time = measure_time(repeat, bm.call, segment.bottomupsegment, data_copy, fit.regression, fit.sumsquared_error_regr, max_error)
            rmse = np.sqrt(((pls_data - data) ** 2).mean())
            correlation = pls_data.corr(data)
            seg = util.get_no_segments(pls_data)

            update_metrics('bur', rmse, correlation, run_time, seg)

            # Top-down with Interpolation
            log.info("Top-down with Interpolation")
            pls_data = bm.call(segment.topdownsegment, data_copy, fit.interpolate, fit.sumsquared_error_int, max_error)

            run_time = measure_time(repeat, bm.call, segment.topdownsegment, data_copy, fit.interpolate, fit.sumsquared_error_int, max_error)
            rmse = np.sqrt(((pls_data - data) ** 2).mean())
            correlation = pls_data.corr(data)
            seg = util.get_no_segments(pls_data)

            update_metrics('tdi', rmse, correlation, run_time, seg)

            # Top-down with Regression
            log.info("Top-down with Regression")
            pls_data = bm.call(segment.topdownsegment, data_copy, fit.regression, fit.sumsquared_error_regr, max_error)

            run_time = measure_time(repeat, bm.call, segment.topdownsegment, data_copy, fit.regression, fit.sumsquared_error_regr, max_error)
            rmse = np.sqrt(((pls_data - data) ** 2).mean())
            correlation = pls_data.corr(data)
            seg = util.get_no_segments(pls_data)

            update_metrics('tdr', rmse, correlation, run_time, seg)

            log.info(metrics)

        except Exception as e:
            log.info('EXCEPTION\n{0}\n{1}'.format(path, e))
            print(traceback.format_exc())
            continue

        df_dict.update({trajectory.path: metrics})

        if limit and i >= limit: break
        else: i += 1


    log.info("Saving...")
    panel = pnd.Panel(df_dict)
    panel.to_pickle("panel.p")
