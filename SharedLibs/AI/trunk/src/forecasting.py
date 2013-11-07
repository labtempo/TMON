'''
Created on Jan 14, 2013

@author: giulio
'''
from SharedLibs.tracetools import TraceReader
from collections import deque
import filters
import matplotlib
from filters import PerceptronBase, MultivariateFilter
import math
matplotlib.use('QT4Agg')
from matplotlib import pyplot
import sys
import time

DEBUG = True
MULTIVARIATE = True
MODE = 'avg' # available modes: avg, max
RMSE = True
PLOT = True

TIME_MULT = 60


def _calc_error(observation, prediction, error_method, multivariate):
    if multivariate:     
        obs_len = len(observation)           
        if MODE == 'avg':                    
            error = sum(filters.error(observation[i], prediction[i], error_method) for i in xrange(obs_len))\
                    / obs_len
        elif MODE == 'max':
            error = max(filters.error(observation[i], prediction[i], error_method) for i in xrange(obs_len))
        else:
            raise Exception("Uknown mode %s" % MODE)
    else:
        error = filters.error(observation, prediction, error_method)
    return error


def calc_errors(timeseries_length, errors_to_calculate, results, multivariate=False, offset=0):    
    # calculate errors cutting out the training data        
    errors = [list() for _i in xrange(len(errors_to_calculate))]
    predicted_data = []
    observed_data = []
        
    for i in xrange(timeseries_length):        
        observation, prediction = results[i]
        
        predicted_data.append(prediction[0:1])
        observed_data.append(observation[0:1])
        
        for k in xrange(len(errors_to_calculate)):
            error_method = errors_to_calculate[k]
            error = _calc_error(observation, prediction, error_method, multivariate)
            errors[k].append(error)
    
    if PLOT:
        pyplot.plot(observed_data[offset:], '-')
        pyplot.plot(predicted_data[offset:], '-')
        pyplot.show()
    
    assert len(errors[0]) == timeseries_length
    
    return errors


def file_iter(file_obj):
    for line in file_obj:
        line = line.strip()
        if line and not line.startswith("#"):
            tokens = line.split()
            yield map(float, tokens)


def calc_spirit_errors(timeseries_length, errors_to_calculate, lag, results, \
                       weights_filename, trace_filename):
    '''
    @todo: make sure that the weight vector matches the expected order
    '''
    # calculate errors cutting out the training data        
    errors = [list() for _i in xrange(len(errors_to_calculate))]
        
    weights_file = open(weights_filename) # spirit weights
    trace_file = open(trace_filename)     # real trace with multiple series
    predicted_data = []
    observed_data = []
    
    try:
        weights_file_iter = file_iter(weights_file)
        trace_file_iter = TraceReader(trace_filename).parse()
        # advance lag
        for _i in xrange(lag):
            trace_file_iter.next()
            for k in xrange(len(errors_to_calculate)):
                errors[k].append(0)
        
        for i in xrange(timeseries_length - lag):
            w = weights_file_iter.next()            
            _y, predicted_y = results[i]
                                            
            reconstructed_x = [predicted_y * w[j] for j in xrange(1, len(w))] # skip timestamp
            x = [v for k, v in trace_file_iter.next().iteritems() if k != "timestamp"]
                        
            predicted_data.append(reconstructed_x[:1])
            observed_data.append(x[:1])
                        
            for k in xrange(len(errors_to_calculate)):
                error_method = errors_to_calculate[k]
                error = _calc_error(x, reconstructed_x, error_method, True)                
                errors[k].append(error)
    finally:
        weights_file.close()
        trace_file.close()
    
    if PLOT:
        pyplot.plot(observed_data, '-')
        pyplot.plot(predicted_data, '-')
        pyplot.show()
    
    assert len(errors[0]) == timeseries_length, "%d != %d" % (len(errors[0]), timeseries_length)
    
    return errors


def get_data(data, mote_id, tr, multivariate=False):
    if tr.file_type == 'txt':
        assert not multivariate
        return data[3]
    if multivariate:
        return [data[key] for key in data.iterkeys() if key != "timestamp"]
    
    return data[mote_id]


def main(args):
    if len(args) < 2:
        print "Usage: python %s {trace path} [-s (spirit mode) {weights path} {original trace path}]" % (args[0])
        exit()
    
    input_path = args[1]
    weights_path = None
    original_trace_path = None
    
    spirit_mode = '-s' in args
    if spirit_mode:
        assert not MULTIVARIATE
        
        spirit_mode_index = args.index('-s')
        weights_path = args[spirit_mode_index + 1]
        original_trace_path = args[spirit_mode_index + 2]
     
    tr = TraceReader(input_path)
    
    lag = int(5 * TIME_MULT) # time units (seconds)
    errors_to_calculate = (filters.MSE, filters.MAE)
    
    #filter_args = {"alpha": 9 * 1e-1, "beta": 2 * 1e-2, "k": lag}
    #filter_args = {"alpha": 4 * 1e-1}
    #filter_args = {"num_last_measures" : 7, "learning_rate" : 1e-4, "lag": lag, "dataset_size": 1}
    #filter_args = {"dataset_size": 2 * TIME_MULT, "lag": lag, "order": 2}
    #filter_args = {"dataset_size": sys.maxint, "order": 1, "lag": lag, "optimize": False, \
    #               "c": 0, "phi": [1]}
    filter_args = {"lag": lag, "window_size": 3 * TIME_MULT}
    #filter_args = {}
    #filter_cls = filters.ExpAvg
    #filter_cls = filters.HoltFilter
    filter_cls = filters.AdaptableHoltFilter
    #filter_cls = filters.DummyFilter
    #filter_cls = filters.SigmoidPerceptron
    #filter_cls = filters.HardLearningLinearPerceptron
    #filter_cls = filters.LinearPerceptron
    #filter_cls = filters.MultiLayerPerceptron
    #filter_cls = filters.RollingPerceptron
    #filter_cls = filters.LazyRollingPerceptron
    #filter_cls = filters.LazyLinearPerceptron
    #filter_cls = filters.FiniteDiffPerceptron
    #filter_cls = filters.DiffPerceptron
    #filter_cls = filters.Oracle
    #filter_cls = filters.Bote
    #filter_cls = filters.SmoothingBote
    #filter_cls = filters.AdaptableARFilter
    #filter_cls = filters.ARFilter
    
    if filter_cls == filters.Oracle:             
        filter_args = {'trace_path': input_path, "lag": lag}
    
    if MULTIVARIATE:
        forecaster = MultivariateFilter(filter_cls, filter_args, len(tr.arff_attributes) - 1) # ignore timestamp
    else:
        forecaster = filter_cls(**filter_args)    
    
    mote_id = "mote_239"
    offset = lag + forecaster.training_delay
    desired_offset = 12 * TIME_MULT
    offset = max(offset, desired_offset)
        
    print "# INFO"
    print "# Lag: %d" % (lag, )
    print "# Errors to calculate: %s" % (", ".join(filters.ERROR_TO_STR[x] for x in errors_to_calculate), )
    print "# Forecaster: %s" % (forecaster, )
    print "# Offset: %d" % (offset, )
        
    start_time = time.time()
    
    results = []
    
    print "Creating buffer..."
    # creates a buffer that consists of the length of the lag window
    data_gen = tr.read()
    
    # fill buffer
    data_buffer = deque(maxlen=lag + 1)
    for _i in xrange(lag + 1):
        data = data_gen.next() # exclude timestamp
        data_buffer.append(get_data(data, mote_id, tr, multivariate=MULTIVARIATE))
    
    print "Making predictions..."            
    # store observations and predictions
    count = 0
    for data in data_gen:
        observation = data_buffer[-1]
        prediction = forecaster.apply(data_buffer[0])
        results.append((observation, prediction))        
        data_buffer.append(get_data(data, mote_id, tr, multivariate=MULTIVARIATE))
        count += 1
        if count % 500 == 0 and isinstance(forecaster, PerceptronBase):
            print "%8d: %s" % (count, forecaster.debug()), len(forecaster.data)
    
    '''
    for fc in forecaster.filters:
        fc.optimize_parameters(fc._data, fc._model)
        print [val / 1e+11 for val in fc._model.itervalues()]
    '''
    
    print "Calculating errors..."
    timeseries_length = len(results)
    
    if spirit_mode:
        errors = calc_spirit_errors(timeseries_length, errors_to_calculate, lag, results, weights_path, original_trace_path)
    else:
        errors = calc_errors(timeseries_length, errors_to_calculate, results, multivariate=MULTIVARIATE, offset=offset)
    
        
    print "# RESULTS"    
    # create averages                
    for k in xrange(len(errors_to_calculate)):
        assert len(errors[k]) == timeseries_length
        
        if MODE == 'avg':
            avg_error = sum(errors[k][offset:]) / (timeseries_length - offset)
        elif MODE == 'max':
            avg_error = max(errors[k][offset:])
                    
        if errors_to_calculate[k] == filters.MSE and RMSE:
            avg_error = math.sqrt(avg_error)
            print "(RMSE mode)"
        print "%s: %f" % (filters.ERROR_TO_STR[errors_to_calculate[k]], avg_error)
    
    print "\nElapsed: %f secs" % (time.time() - start_time)
    
    
if __name__ == '__main__':
    main(sys.argv)
    #main(['forecasting', '/home/giulio/Dropbox/Projeto Sensores/experiments/samples_20_02_13_15h05m47s/inlet.arff', \
    #      '/home/giulio/Dropbox/Projeto Sensores/experiments/samples_20_02_13_15h05m47s/hidden_vars.txt', \
    #      '/home/giulio/Dropbox/Projeto Sensores/experiments/samples_20_02_13_15h05m47s/blame.txt'])
