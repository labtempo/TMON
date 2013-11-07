'''
Created on May 1, 2013

@author: Giulio
'''
from batch_exps import runner
import filters
import os

if __name__ == '__main__':
    #working_dir = '/home/giulio/Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut2/cmp01'
    working_dir = 'D:/Giulio/My Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut3'
    trace_path = os.path.join(working_dir, 'cut.arff')
    hidden_vars_path = os.path.join(working_dir, 'hidden_vars.txt')
    weights_path = os.path.join(working_dir, 'blame.txt')
    hidden_vars_path = weights_path = None

    tick_value = 1
    lo_temp = hi_temp = 30.0
    trace_start_offset = 60 * 60
    mote_id = 'mote_249'
    #mote_id = None
    lag_min = lag_max = 3
    #lag_max = 5
    min_alarm_window = 1 * 60
    max_alarm_window = 10 * 60

    r = runner.ExpRunner(trace_path, lo_temp, hi_temp, trace_start_offset, tick_value, mote_id=mote_id, \
                         hidden_vars_path=hidden_vars_path, weights_path=weights_path, min_alarm_window=min_alarm_window, \
                            max_alarm_window=max_alarm_window)
    r.setup()

    for lag in xrange(lag_min, lag_max + 1):
        s_lag = lag * 60 / tick_value
        #forecaster = filters.DummyFilter()
        #forecaster = filters.ExpFilter(alpha=0.1)
        forecaster = filters.AdaptableHoltFilter(s_lag, window_size=12 * 60)
        #forecaster = filters.AdaptableARFilter(s_lag, dataset_size=5 * 60)
        #forecaster = filters.RollingPerceptron(learning_rate=1e-6, num_last_measures=1, lag=s_lag)
        #forecaster = filters.LinearPerceptron(learning_rate=1e-6, num_last_measures=1, lag=s_lag, dataset_size=1)
        print "Lag:", lag
        result = r.run(forecaster, s_lag, plot=True)
        r.print_results(result)
        print ''