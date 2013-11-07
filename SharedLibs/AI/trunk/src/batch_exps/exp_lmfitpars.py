'''
Created on May 10, 2013

@author: giulio
'''
from batch_exps import runner
import filters
import os


def build_perceptron(perceptron_cls, learning_rate, num_last_measures):
    return lambda lag: perceptron_cls(learning_rate=learning_rate, num_last_measures=num_last_measures, lag=lag)


if __name__ == '__main__':
    #working_dir = '/home/giulio/Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut3'
    working_dir = 'D:/Giulio/My Dropbox/Projeto Sensores/experiments/falta_de_luz/energy_saving/cut3'
    trace_path = os.path.join(working_dir, 'cut.arff')    
    hidden_vars_path = weights_path = None
    
    lo_temp = hi_temp = 30.0
    trace_start_offset = 60 * 60
    mote_id = 'mote_249'
    tick_value = 1
            
    lag = 5
    s_lag = lag * 60
    dataset_size_list = [i * 60 for i in xrange(1, 10 + 1)] 
    
    exps = [
            ('AdaptableHolt', lambda lag, minimize_kws, dataset_size: \
             filters.AdaptableHoltFilter(lag, window_size=dataset_size, minimize_kws=minimize_kws)), \
            #('AdaptableAR', lambda lag, minimize_kws, dataset_size: \
            # filters.AdaptableARFilter(lag, dataset_size=dataset_size, minimize_kws=minimize_kws)), \
           ]
            
    with open('exp_lmfitpars_results.txt', 'w') as out:
        out.write('#lag #dataset_size #RMSE #lmfit_usage #lmfit_calls\n')
        name_prefix = ''
        
        r = runner.ExpRunner(trace_path, lo_temp, hi_temp, trace_start_offset, tick_value, mote_id=mote_id, \
                         hidden_vars_path=hidden_vars_path, weights_path=weights_path)
        r.setup()
    
        for name, builder in exps:
            out.write('# %s:\n' % (name_prefix + name))
            for dataset_size in dataset_size_list:  
                minimize_kws = {'gtol':0, 'xtol': 0}
                forecaster = builder(s_lag, minimize_kws, dataset_size)
                _mat, _recall, _far, rmse = r.run(forecaster, s_lag, plot=False)
                lmfit_use_ratio = (forecaster.lmfit_calls - forecaster.lmfit_fails) / float(forecaster.lmfit_calls)
                
                out.write('%d\t%d\t%f\t%f\t%d\n' % (lag, dataset_size, rmse, lmfit_use_ratio, forecaster.lmfit_calls))
                out.flush()
            out.write("\n\n")
    
        hidden_vars_path = os.path.join(working_dir, 'hidden_vars.txt')
        weights_path = os.path.join(working_dir, 'blame.txt')
        name_prefix = "SPIRIT + "