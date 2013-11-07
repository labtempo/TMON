'''
Created on May 29, 2013

@author: Giulio

Regression for the observations (no predictor).
'''
from batch_exps import runner
import filters
import os

def build_perceptron(perceptron_cls, learning_rate, num_last_measures):
    return lambda lag: perceptron_cls(learning_rate=learning_rate, num_last_measures=num_last_measures, lag=lag, \
                                      dataset_size=1)

if __name__ == '__main__':
    #working_dir = '/home/giulio/Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut2/cmp01'
    working_dir = 'D:/Giulio/My Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut3'
    trace_path = os.path.join(working_dir, 'cut.arff')
    #hidden_vars_path = os.path.join(working_dir, 'hidden_vars.txt')
    #weights_path = os.path.join(working_dir, 'blame.txt')
    hidden_vars_path = weights_path = None
    
    tick_value = 1
    lo_temp = hi_temp = 30.0
    trace_start_offset = 60 * 60
    mote_id = 'mote_249'    
    s_lag = 1 * 60    
    regression_windows = [i * 60 for i in xrange(0, 40 + 1)]
    regression_windows[0] = 2
    use_predictions = False
    
    exps = [('Naive (observation)', lambda lag: filters.DummyFilter()), \
            ('RollingPerceptron', build_perceptron(filters.RollingPerceptron, 1e-7, 1)), \
            ('AdaptableHolt', lambda lag: filters.AdaptableHoltFilter(lag, window_size=9 * 60)), \
           ]
    
    with open('exp_regression_results.txt', 'w') as f:
        for pred_name, builder in exps:
            forecaster = builder(s_lag)
            
            r = runner.ExpRunner(trace_path, lo_temp, hi_temp, trace_start_offset, tick_value, mote_id=mote_id, \
                                 hidden_vars_path=hidden_vars_path, weights_path=weights_path)
            r.setup()
            r.run(forecaster, s_lag)
            
            f.write('# %s\n' % pred_name)
            f.write('#regression_window #RMSE\n')
            for regression_window in regression_windows:                
                alarm_forecasts = r.calc_alarm_forecast(r.predictions_cache, s_lag, forecaster.training_delay, \
                                                        regression_window, \
                                                        use_predictions=use_predictions)
                alarm_stats = r.calc_alarm_forecast_stats(alarm_forecasts)            
                rmse = alarm_stats[-1]
                
                print 'RW:', regression_window
                print rmse
                
                f.write('%d %f\n' % (regression_window, rmse))
                f.flush()
            
            f.write('\n\n')
            use_predictions = True