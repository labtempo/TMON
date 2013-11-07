'''
Created on Feb 10, 2013

@author: Giulio
'''
import sys
import datetime
from matplotlib import pyplot, dates
import anomaly_detector
import numpy as np
import spirit
from SharedLibs import tracetools


def read_known_anomalies_file(filename):
    '''
    Format:
    <timestamp_start> <timestamp_end> 
    '''
    anomalies = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line:
                anomalies.append(map(float, line.split()))
    return anomalies


def detect_anomalies(trace_filename, detector, motes_to_ignore=tuple()):
    '''
    @return: summarized, anomaly_levels
    '''
    anomaly_levels = []
    summarized_series = []
    sp = spirit.Spirit(l=1., k=1, fixed_k=True)
    tr = tracetools.TraceReader(trace_filename, motes_to_ignore=motes_to_ignore)
    trace_start = -1
    for data in tr.read():
        if trace_start < 0:
            trace_start = data['timestamp']
        data = np.matrix([v for k, v in data.iteritems() if k != "timestamp"]).T
        k, w, Y = sp.update(data)
        summ_Y = Y[0, 0]
        anomaly_level = detector.apply(summ_Y)
        anomaly_levels.append(anomaly_level)    
        summarized_series.append(summ_Y)
    
    return summarized_series, anomaly_levels, trace_start


def plot(ds, anomaly_levels, summarized_series, trace_start, known_anomalies, anomaly_threshold):
    fig = pyplot.figure()
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twinx()
    
    ax2.plot_date(ds, anomaly_levels, "-", color="red")
    ax1.plot_date(ds, summarized_series, "-", linewidth=3)
    
    for anomaly_start, anomaly_length in known_anomalies:
        ax1.plot_date((datetime.datetime.fromtimestamp(anomaly_start), \
                       datetime.datetime.fromtimestamp(anomaly_start + anomaly_length)), \
                       [summarized_series[min(int(anomaly_start - trace_start), len(summarized_series) - 1)] * 1.02] * 2, \
                       '.-', color="purple", linewidth=3)
    
    # plot anomaly_threshold
    ax2.plot_date(ds, [anomaly_threshold] * len(ds), '--', color="red")    
    
    ax1.set_ylabel('SPIRIT Y')
    ax2.set_ylabel('Anomaly level')
    pyplot.grid(True)
    pyplot.show()


def validate_results(known_anomalies, anomaly_threshold, anomaly_levels, trace_start):
    detected_anomaly_time = 0
    correctly_detected_anomaly_time = 0
    identified_anomalies = set()
    overdetections = 0
    anomaly_phase = False
    
    for i in xrange(len(anomaly_levels)):
        anomaly_level = anomaly_levels[i]
        if anomaly_level > anomaly_threshold:            
            detected_anomaly_time += 1
            current_time = trace_start + i
            
            # look for a known_anomaly
            found_known_anomaly = False
            for known_anomaly_start, known_anomaly_length in known_anomalies:
                if known_anomaly_start < current_time < known_anomaly_start + known_anomaly_length:
                    correctly_detected_anomaly_time += 1
                    found_known_anomaly = True
                    break
            if found_known_anomaly:
                identified_anomalies.add(known_anomaly_start)
            elif not anomaly_phase:
                overdetections += 1
            anomaly_phase = True
        else:
            anomaly_phase = False
    
    return detected_anomaly_time, correctly_detected_anomaly_time, identified_anomalies, overdetections


def main(args):
    #trace_filename =     r"D:\Giulio\My Dropbox\Projeto Sensores\experiments\temperatura\sala_servidores\samples_20_02_13_15h05m47s.arff"
    #anomalies_filename = r"D:\Giulio\My Dropbox\Projeto Sensores\experiments\temperatura\sala_servidores\samples_20_02_13_15h05m47s_anomalies.txt"
    #trace_filename =     r"D:\Giulio\My Dropbox\Projeto Sensores\experiments\temperatura\sala_servidores\samples_07_02_13_10h40m26s.arff"
    #anomalies_filename = r"D:\Giulio\My Dropbox\Projeto Sensores\experiments\temperatura\sala_servidores\samples_07_02_13_10h40m26s_anomalies.txt"
    
    if len(args) < 2:
        print "Usage: python %s {trace filename} {anomalies filename}" % (args[0],)
        exit()
    
    trace_filename = args[1]
    anomalies_filename = args[2]
    
    N = 10 # data buffer size for a word
    n = 5  # size of a letter
    
    '''
    Number of words in each window
    '''
    lag_window = 200
    lead_window = 100
    
    anomaly_threshold = 0.08    
    alphabet = "abc"
    bitmap_level = 2
    detector = anomaly_detector.TSBitmaps(lag_window, lead_window, anomaly_threshold, N, n, alphabet, bitmap_level)    
    #detector = anomaly_detector.CUSUMDetector(anomaly_threshold=0.5, L=0.001, mu=0, alpha=0.01)
    
    offset = detector.apply_threshold
    if isinstance(detector, anomaly_detector.TSBitmaps):
        offset += N + lead_window + max(lead_window, lag_window)
    print "Lateness: %.2f min" % (offset / 60.)
    
    motes_to_ignore = tuple()
    
    known_anomalies = read_known_anomalies_file(anomalies_filename)
    
    print "Detecting anomalies..."
    summarized_series, anomaly_levels, trace_start = detect_anomalies(trace_filename, detector, motes_to_ignore)
    
    print "Validating..."    
    del summarized_series[-offset:]
    del anomaly_levels[:offset]
    
    ds = dates.date2num([datetime.datetime.fromtimestamp(trace_start + i) \
                                           for i in xrange(len(summarized_series))])
    
    total_anomaly_time = float(sum(known_anomalies[i][1] for i in xrange(len(known_anomalies))))    
    try:
        while True:
            detected_anomaly_time, correctly_detected_anomaly_time, identified_anomalies, overdetections \
                = validate_results(known_anomalies, anomaly_threshold, anomaly_levels, trace_start)
                        
            print "Anomaly threshold is %.2f" % anomaly_threshold
            print "Detected anomaly time: %d" % detected_anomaly_time
            #print "Overdetection rate: %.4f" % ((detected_anomaly_time - total_anomaly_time) / total_anomaly_time)
            print "Correctly detected anomaly time: %d, %.4f" % (correctly_detected_anomaly_time, \
                                                                 correctly_detected_anomaly_time / total_anomaly_time)
            print "Identified anomalies: %d out of %d" % (len(identified_anomalies), len(known_anomalies))
            print "Overdetected anomalies: %d" % overdetections
            print "Detection score: %d" % (len(identified_anomalies) * 3 - overdetections)
            
            plot(ds, anomaly_levels, summarized_series, trace_start, known_anomalies, anomaly_threshold)
            
            
            print "Type a new anomaly threshold:"
            anomaly_threshold = float(raw_input())
    except SystemExit:
        pass
    finally:
        print "End."

if __name__ == '__main__':
    main(sys.argv)