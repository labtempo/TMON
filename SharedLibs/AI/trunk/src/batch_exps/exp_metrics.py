'''
Created on May 10, 2013

@author: giulio
'''
from batch_exps import runner
import filters
import os


def build_perceptron(perceptron_cls, learning_rate, num_last_measures):
    return lambda lag: perceptron_cls(learning_rate=learning_rate, num_last_measures=num_last_measures, lag=lag, \
                                      dataset_size=1)


if __name__ == '__main__':
    #working_dir = '/home/giulio/Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut3'
    working_dir = 'D:/Giulio/My Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut3'
    trace_path = os.path.join(working_dir, 'cut.arff')    
    hidden_vars_path = weights_path = None
    
    lo_temp = hi_temp = 30.0
    trace_start_offset = 60 * 60
    mote_id = 'mote_249'
    tick_value = 1
    alarm_forecast_points = 10 * 60
    
    lag_min = 1
    lag_max = 20
    
    exps = [#('Naive', lambda lag: filters.DummyFilter()), \
            #('RollingPerceptron', build_perceptron(filters.RollingPerceptron, 1e-6, 1)), \
            ('LinearPerceptron', build_perceptron(filters.LinearPerceptron, 1e-5, 1)), \
            #('AdaptableHolt', lambda lag: filters.AdaptableHoltFilter(lag, window_size=12 * 60)), \
            #('AdaptableAR', lambda lag: filters.AdaptableARFilter(lag, dataset_size=5 * 60)), \
           ]
            
    with open('exp_metrics_results.txt', 'w') as out:
        out.write('#lag #prediction_rmse #adv_notice #earliness #lateness #adv_notice_error #early_alarms #late_alarms \n')
        name_prefix = ''
        
        for i in xrange(2):
            r = runner.ExpRunner(trace_path, lo_temp, hi_temp, trace_start_offset, tick_value, mote_id=mote_id, \
                                 hidden_vars_path=hidden_vars_path, weights_path=weights_path)
            r.setup()
        
            for name, builder in exps:
                out.write('# %s:\n' % (name_prefix + name))
                for lag in xrange(lag_min, lag_max + 1):
                    s_lag = lag * 60
                                    
                    forecaster = builder(s_lag)
                    stats = r.run(forecaster, s_lag, plot=False)
                    
                    out.write('%d\t%f\t%f\t%f\t%f\t%f\t%d\t%d\n' % \
                              (lag, \
                               stats['pred_error'], \
                               stats['mean_adv_time'], \
                               stats['mean_earliness'], \
                               stats['mean_lateness'], \
                               stats['mean_adv_error'], \
                               stats['early_alarms'], \
                               stats['late_alarms']))
                    out.flush()
                out.write("\n\n")
        
            hidden_vars_path = os.path.join(working_dir, 'hidden_vars.txt')
            weights_path = os.path.join(working_dir, 'blame.txt')
            name_prefix = "SPIRIT + "