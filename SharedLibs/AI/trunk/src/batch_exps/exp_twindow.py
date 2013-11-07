'''
Created on May 10, 2013

@author: giulio
'''
from batch_exps import runner
import filters
import os


if __name__ == '__main__':
    #working_dir = '/home/giulio/Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut3'
    working_dir = 'D:/Giulio/My Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut3'
    trace_path = os.path.join(working_dir, 'cut.arff')    
    hidden_vars_path = weights_path = None
    
    lo_temp = hi_temp = 30.0
    trace_start_offset = 60 * 60
    mote_id = 'mote_249'
    tick_value = 1
    
    r = runner.ExpRunner(trace_path, lo_temp, hi_temp, trace_start_offset, tick_value, mote_id=mote_id, \
                         hidden_vars_path=hidden_vars_path, weights_path=weights_path, alarm_forecast_points=0)
    r.setup()
    
    # values in minutes
    lag_min = 1
    lag_max = 10
    dataset_min = 1
    dataset_max = 20
    
    exps = [('AdaptableAR', lambda lag, dataset_size: filters.AdaptableARFilter(lag, dataset_size)), \
            ('AdaptableHolt', lambda lag, dataset_size: filters.AdaptableHoltFilter(lag, window_size=dataset_size))]
        
    with open('exp_twindow_results.txt', 'w') as out:
        out.write('# dataset_size # lag # RMSE\n')
        
        for name, builder in exps:
            out.write('# %s\n' % name)
            errors = {} # dict: dataset_size: errors
            for dataset_size in xrange(dataset_min, dataset_max + 1):
                errors[dataset_size] = []
                for lag in xrange(lag_min, lag_max + 1):
                    s_lag = lag * 60 # lag in seconds
                    forecaster = builder(s_lag, dataset_size * 60)
                    result = r.run(forecaster, s_lag, plot=False)
                    print result
                    errors[dataset_size].append(result[3])
                    
                    out.write('%d\t%d\t%f\n' % (dataset_size, lag, result[3]))
                    out.flush()
            
            # find minimum:
            min_dataset_size = dataset_min
            min_dataset_error = sum(errors[dataset_min])
            for dataset_size in xrange(dataset_min + 1, dataset_max + 1):
                total_error = sum(errors[dataset_size])
                if total_error < min_dataset_error:
                    min_dataset_error = total_error
                    min_dataset_size = dataset_size
                    
            out.write("# Best (general) dataset size is: %d minutes\n\n\n" % min_dataset_size)
            out.flush()