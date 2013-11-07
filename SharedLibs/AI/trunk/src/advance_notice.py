'''
Created on Jan 20, 2013

@author: Giulio
'''
from SharedLibs.tracetools import TraceReader # @UnresolvedImportError
import datetime
import filters
import matplotlib
from filters import MSE
import math
matplotlib.use('QT4Agg')
import matplotlib.pyplot as pyplot
import sys
from forecasting import calc_errors


PLOT = True


def trim_emergencies(start, emergencies, end):
    emergencies = emergencies[:]
    
    # conform all emergencies to the [start, end] interval
    for i in xrange(len(emergencies)):
        if emergencies[i][2] > end:
            emergencies[i] = (emergencies[i][0], emergencies[i][1], end)
        if emergencies[i][0] < start:
            emergencies[i] = (start, emergencies[i][1], emergencies[i][2])
    
    # ignore invalid emergencies
    new_emergencies = []
    for emergency in emergencies:
        if emergency[0] <= emergency[2]: # start must be less than end
            new_emergencies.append(emergency)
    
    return new_emergencies


def join_emergencies(emergencies, delta):
    index = 0
    
    while index < len(emergencies) - 1 and len(emergencies) > 1:
        curr_em = emergencies[index]
        next_em = emergencies[index + 1]
        emergency_gap = next_em[0] - curr_em[2]
        
        if emergency_gap < delta:
            curr_length = curr_em[2] - curr_em[0]
            next_length = next_em[2] - next_em[0]
            
            # the new temperature will be equal to the one used on the longest interval
            joined_temp = curr_em[1] if curr_length > next_length else next_em[1]
            
            joined = (curr_em[0], joined_temp, next_em[2])
                        
            del emergencies[index: index + 2]
                                    
            emergencies.insert(index, joined)
        else:
            index += 1
    
    return emergencies


def spirit_closure(weights_path, hidden_vars_path, forecaster=None):
    weights_file = open(weights_path)
    hidden_vars_file = open(hidden_vars_path)
    predictions = []
    
    if not forecaster:
        forecaster = lambda y: y
    
    weights_file.readline() # skip the header
    header = hidden_vars_file.readline()[1:] # skip '#'
    header = header.split()
    
    def spirit_preproc(data, mote_id):
        weights = map(float, weights_file.readline().split())
        y = map(float, hidden_vars_file.readline().split())
        
        mote_index = header.index(mote_id)
                
        predicted_y = forecaster(y[1])        
        reconstructed_data = [predicted_y * weights[i] for i in xrange(1, len(weights))]
        
        predicted = reconstructed_data[mote_index]
        predictions.append(predicted)
        
        return predicted
    
    return spirit_preproc, predictions


def confirmation_trigger(trace_reader, lower_temp_threshold, higher_temp_threshold, mote_id, req_confirmations, \
                         preproc_function=None):
    
    if not preproc_function:
        preproc_function = lambda data, mote_id: data[mote_id]
    
    confirmations = 0
    emergency_temp = 0
    emergency_start = 0
    emergency_end = 0
    confirmed = False
    
    for data in trace_reader:
        temp = preproc_function(data, mote_id)
        
        if temp > higher_temp_threshold:      
            confirmations = min(req_confirmations, confirmations + 1)            
            if not confirmed and confirmations == req_confirmations:                
                emergency_temp = temp
                emergency_start = data['timestamp']
                confirmed = True
                
        elif temp < lower_temp_threshold:
            confirmations = max(0, confirmations - 1)
            
        if confirmed and confirmations == 0:
            emergency_end = data['timestamp']      
            yield (emergency_start, emergency_temp, emergency_end)
            confirmed = False
                    
    if confirmed:
        emergency_end = data['timestamp']      
        yield (emergency_start, emergency_temp, emergency_end)        
    

def thermocast_analyze_predictions(triggered_emergencies, emergencies, lag):
    mat = 0.0
    
    for em_start, _em_temp, _em_end in emergencies:
        dt = 0.0
        
        for tr_start, _tr_temp, _tr_end in triggered_emergencies:
            curr_dt = em_start - tr_start + lag
            if curr_dt > dt:
                dt = curr_dt
        
        mat += dt
    
    mat /= len(emergencies)
    
    return mat


def xor_analyze_predictions(triggered_emergencies, emergencies):
    underdetected_time = 0
    overdetected_time = 0
    detected_time = 0
    
    for em_start, _1, em_end in emergencies:
        intersection = False # marks at least one intersection has occurred
        for tr_start, _2, tr_end in triggered_emergencies:
            if tr_start <= em_start <= tr_end and tr_start <= em_end <= tr_end:
                intersection = True
                overdetected_time += em_start - tr_start
                overdetected_time += tr_end - em_end
                detected_time += em_end - em_start
            elif em_start <= tr_start <= em_end and em_start <= tr_end <= em_end:
                intersection = True
                underdetected_time += tr_start - em_start
                underdetected_time += em_end - tr_end
                detected_time += tr_end - tr_start            
            elif tr_start <= em_start <= tr_end:
                intersection = True
                underdetected_time += em_end - tr_end
                overdetected_time  += em_start - tr_start
                detected_time += tr_end - em_start
            elif tr_start <= em_end <= tr_end:
                intersection = True
                underdetected_time += tr_start - em_start
                overdetected_time  += tr_end - em_end
                detected_time += em_end - tr_start
        
        if not intersection:
            underdetected_time += em_end - em_start
    
    # Look for predictions that don't intersect with anybody
    for tr_start, _2, tr_end in triggered_emergencies:
        intersection = False
        for em_start, _1, em_end in emergencies:
            if (tr_start <= em_start <= tr_end) or (tr_start <= em_end <= tr_end) \
                or (em_start <= tr_start <= em_end) or (em_start <= tr_end <= em_end):
                intersection = True
                
        if not intersection:
            overdetected_time += tr_end - tr_start
        
    return underdetected_time, overdetected_time, detected_time


def calc_avg_tardiness(emergencies, triggered_emergencies):
    MAX_DIST = 30 * 60
    
    count = 0
    acc_tardiness = 0.0
    if len(triggered_emergencies) > 0:
        for emergency_start, _1, _2 in emergencies:
            # find closest match
            closest_match = triggered_emergencies[0][0]
            for tr_emergency_start, _3, _4 in triggered_emergencies[1:]:
                if abs(tr_emergency_start - emergency_start) < abs(closest_match - emergency_start):
                    closest_match = tr_emergency_start
            
            dist = closest_match - emergency_start
            if abs(dist) < MAX_DIST:
                count += 1           
                acc_tardiness += dist
    
    if count == 0:
        return 0.0
        
    return acc_tardiness / count


def compress_trace(trace_reader, factor, series_id):
    data = []
    if factor == 1:
        for values in trace_reader:
            if isinstance(values, dict):
                data.append({series_id: values[series_id], "timestamp": values['timestamp']})
            else: #@attention: hack
                data.append({series_id: float(values[3]), "timestamp": values[0]})
        return data
    
    acc = 0.0
    count = 1
    for values in trace_reader:
        acc += values[series_id]
        if count % factor == 0:
            timestamp = values['timestamp'] - factor
            avg = {series_id: acc / factor, "timestamp": timestamp}
            data.append(avg)
            acc = 0.0
        count += 1
    
    return data


def main(args):
    if len(args) < 2:
        print "Usage: python %s {trace path} [-s (spirit mode) {weights path} {original trace path}]" % (args[0], )
        exit()
    
    input_path = args[1]
    
    tr = TraceReader(input_path, supress_repetitions=False, auto_interpolation=False, suppress_rapid_changes=False, \
                      motes_to_ignore=[])
    
    emergency_confirmations = 1
    predictor_confirmations = 1
    lower_temp_threshold = 30.0
    higher_temp_threshold = 30.0
    series_id = "mote_244"
    compression_factor = 1
    lag = 10 * 60
    cmp_lag = lag / compression_factor
    delta = 60
    predictor_delta = 0.0
    error_offset = 12 * 60
    
    # Filter config
    #filter_args = {"alpha": 9 * 1e-1, "beta": 8 * 1e-3, "k": cmp_lag}
    #filter_args = {"lag": cmp_lag, "window_size": 2 * 60}
    filter_args = {"lag": cmp_lag, "dataset_size": 2 * 60, "order": 2}    
    #filter_cls = filters.HoltFilter
    #filter_args = {"alpha": 1 * 1e-3}
    #filter_cls = filters.ExpFilter
    #filter_args = {}
    #filter_cls = filters.DummyFilter
    #filter_args = {"learning_rate" : 1 * 1e-3, "lag": cmp_lag, "dataset_size": 1, "num_last_measures": 1}
    #filter_args = {"learning_rate" : 6 * 1e-7, "lag": cmp_lag, "dataset_size": 1, "num_last_measures": 10}
    #filter_cls = filters.LinearPerceptron
    #filter_cls = filters.RollingPerceptron
    #filter_cls = filters.SigmoidPerceptron
    #filter_cls = filters.PerceptronFilterBreno
    #filter_cls = filters.PerceptronFilterPyBrain
    #filter_cls = filters.AdaptableHoltFilter
    filter_cls = filters.AdaptableARFilter
    
    forecaster = filter_cls(**filter_args)
    
    print "# INFO"
    print "# Emergency confirmations: %d" % emergency_confirmations    
    print "# Predictor confirmations: %d" % predictor_confirmations 
    print "# Temperature threshold: %s degrees" % ((lower_temp_threshold, higher_temp_threshold), )
    print "# Series ID: %s" % series_id
    print "# Lag: %d seconds" % lag
    print "# Forecaster: %s" % repr(forecaster)    
    print "# Predictor delta: %f" % predictor_delta
    print "# Compression factor: %d" % compression_factor
    
    if '-s' in args:
        s_index = args.index('-s')
        weights_path = args[s_index + 1]
        hidden_vars_path = input_path
        spirit_preproc, _predictions = spirit_closure(weights_path, hidden_vars_path, None)
    else:
        spirit_preproc = None
    
    print "Compressing trace..."    
    compressed_trace = compress_trace(tr, compression_factor, series_id)
    
    print "Looking for emergencies..."
    emergencies = [e for e in confirmation_trigger(compressed_trace, lower_temp_threshold, higher_temp_threshold, \
                                                   series_id, emergency_confirmations, preproc_function=spirit_preproc)]
               
    train_delay = max(forecaster.training_delay, 1)
    trace_offset = cmp_lag + train_delay
    print "Trace offset:", trace_offset
    
    print "Making predictions..."    
    
    data_gen = iter(compressed_trace)
            
    # Train
    trace_start = -1
    for _ in xrange(train_delay):            
        data = data_gen.next()
        if trace_start < 0:
            trace_start = data['timestamp'] + trace_offset
        forecaster.apply(data[series_id])
    
    assert trace_start >= 0
    
    # Advance notice
    observations = []
    predictions = []
    triggered_emergencies = []
    
    def predictor_preproc_function(data, mote_id):
        temp = data[mote_id]
        observations.append(temp)
        prediction = forecaster.apply(temp)
        predictions.append(prediction)
        return prediction
    
    if '-s' in args:        
        predictor_preproc_function, predictions = spirit_closure(weights_path, hidden_vars_path, forecaster.apply)
    
    for emergency_start, emergency_temp, emergency_end in \
        confirmation_trigger(compressed_trace, lower_temp_threshold + predictor_delta, \
                             higher_temp_threshold - predictor_delta, series_id, predictor_confirmations, \
                             preproc_function=predictor_preproc_function):
        triggered_emergencies.append((emergency_start + lag, emergency_temp, emergency_end + lag))
    
    
    if '-s' in args:
        original_trace_path = args[s_index + 2]
        observations = map(lambda d: d[series_id], compress_trace(TraceReader(original_trace_path), \
                                                                  compression_factor, series_id))
                
    trace_end = trace_start + (len(observations) - cmp_lag)
    emergencies = trim_emergencies(trace_start, emergencies, trace_end)
    triggered_emergencies = trim_emergencies(trace_start, triggered_emergencies, trace_end)
        
    emergencies = join_emergencies(emergencies, delta)
    triggered_emergencies = join_emergencies(triggered_emergencies, delta)
        
    print "Found %d emergencies." % len(emergencies)
    assert len(emergencies) > 0
    
    mat = thermocast_analyze_predictions(triggered_emergencies, emergencies, lag)
    underdetected_time, overdetected_time, detected_time = xor_analyze_predictions(triggered_emergencies, emergencies)
        
    recall = detected_time  / (detected_time + underdetected_time + 1e-100)
    FAR = overdetected_time / (detected_time + overdetected_time  + 1e-100)
    
    del observations[:cmp_lag] # removes data that is not subject to prediction
    del predictions[-cmp_lag:] # removes predictions that cannot be followed by data
            
    total_detection_time = int(sum(e[2] - e[0] for e in emergencies))
                
    timeseries_length = len(observations)    
    errors = calc_errors(timeseries_length, (MSE, ), map(lambda a: ([a[0]], [a[1]]), zip(observations, predictions)), \
                         multivariate=True, offset=error_offset)
    
    rmse = math.sqrt(sum(errors[0]) / (timeseries_length - error_offset))
        
    print "Known emergency time : %d seconds" % total_detection_time                        
    print "Recall               : %.4f" % recall
    print "FAR                  : %.4f" % FAR        
    print "MAT                  : %.4f seconds" % mat
    print "RMSE                 : %.4f" % rmse
    
    # calculate average tardiness:
    #avg_tardiness = calc_avg_tardiness(emergencies, triggered_emergencies)
    #print "Avg tardiness: %.1f seconds" % (avg_tardiness,)
    
    if PLOT:
        print "Plotting..."
        
        pyplot.grid(True)
                        
        dates = matplotlib.dates.date2num([datetime.datetime.fromtimestamp(trace_start + i * compression_factor) \
                                           for i in xrange(len(observations))])
        
        p1, = pyplot.plot_date(dates, observations, '-')
        p2, = pyplot.plot_date(dates, predictions, '-')
        pyplot.plot_date(dates, [lower_temp_threshold] * len(dates), '--', color="red") # temperatura threshold
        pyplot.plot_date(dates, [higher_temp_threshold] * len(dates), '--', color="red") # temperatura threshold
        
        pyplot.plot_date(dates, [lower_temp_threshold + predictor_delta] * len(dates), '--', color="orange") # temperatura threshold
        pyplot.plot_date(dates, [higher_temp_threshold - predictor_delta] * len(dates), '--', color="orange") # temperatura threshold
        
        def plot_emergencies(emergency_list, color, style, offset=0.5):
            for emergency_time, emergency_temp, emergency_end in emergency_list:
                pyplot.plot_date((datetime.datetime.fromtimestamp(emergency_time), \
                                  datetime.datetime.fromtimestamp(emergency_end)), \
                                 [emergency_temp + offset] * 2, style, color=color, linewidth=3)
        
        # plot real emergencies
        plot_emergencies(emergencies, "red", '-', 1)
        
        # plot detected emergencies
        plot_emergencies(triggered_emergencies, "orange", '-', -1)  
        
        pyplot.legend((p2, p1), ("predictions", "observations"))
        pyplot.show()
    
    
if __name__ == '__main__':
    main(sys.argv)
    