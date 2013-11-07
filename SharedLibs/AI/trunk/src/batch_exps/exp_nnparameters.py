'''
Created on May 10, 2013

@author: giulio
'''
'''
Created on May 10, 2013

@author: giulio
'''
from batch_exps import runner
import filters
import os


def build_perceptron(perceptron_cls):
    return lambda learning_rate, num_last_measures, lag: \
        perceptron_cls(learning_rate=learning_rate, num_last_measures=num_last_measures, lag=lag, dataset_size=1)

def build_multilayer():
    return lambda learning_rate, num_last_measures, lag: \
        filters.MultiLayerPerceptron(learning_rate=learning_rate, num_last_measures=num_last_measures, lag=lag, \
                                     topology=(2,))

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
                         hidden_vars_path=hidden_vars_path, weights_path=weights_path)
    r.setup()
    
    # values in minutes
    lag = 5
    s_lag = lag * 60 # lag in seconds
    dataset_size = 1    
    learning_rate_min = 1
    learning_rate_max = 15
    num_last_measures_min = 1
    num_last_measures_max = 10
    
    exps = [('RollingPerceptron', build_perceptron(filters.RollingPerceptron)), \
            #('MultiLayerPerceptron (2)', build_perceptron(filters.MultiLayerPerceptron)), \
            ('LinearPerceptron', build_perceptron(filters.LinearPerceptron)), \
           ]
            
    with open('exp_nnparameters_results.txt', 'w') as out:
        out.write('# num_last_measures # learning_rate # RMSE\n')
        
        for name, builder in exps:
            out.write('# %s\n' % name)
            for num_last_measures in xrange(num_last_measures_min, num_last_measures_max + 1):
                                
                for learning_rate in xrange(learning_rate_min, learning_rate_max + 1):
                    learning_rate = 10 ** -learning_rate
                    params = (learning_rate, num_last_measures, s_lag)
                    
                    print params
                    
                    forecaster = builder(*params)
                    try:
                        result = r.run(forecaster, s_lag)
                        error = str(result[-1])
                        if error == 'nan':
                            error = '?'
                    except Exception as e:
                        print "Exception has occurred:", e
                        error = "?"
                    
                    out.write('%d\t%e\t%s\n' % (num_last_measures, learning_rate, error))
                    out.flush()            