'''
Created on Sep 30, 2012

@author: Giulio
'''
import sys
import numpy as np
import scipy.stats
import collections
from SharedLibs import tracetools
import getopt


class MarkovChain(object):
    PROB_PRECISION = 1e-5
    SMALL_FLOAT = 1e-10
    
    def __init__(self, window_len, state_count):
        assert window_len % 2 == 0
        
        self.window_len = window_len
        self.data_buffer = []
        self.transition_matrix = np.empty(shape=(state_count, state_count), dtype="int")
        self.transition_matrix.fill(self.SMALL_FLOAT)
        self.state_count = state_count
            
    def calc_state_probs(self):
        probs = np.empty(shape=(1, self.state_count))
        probs.fill(1./self.state_count) # initialize with equal probabilities
        
        # normalize transition matrix
        #norm_transition_matrix = self.transition_matrix / np.max(self.transition_matrix)
        norm_transition_matrix = np.empty(shape=self.transition_matrix.shape)
        for i in xrange(norm_transition_matrix.shape[0]):
            norm_transition_matrix[i,:] = self.transition_matrix[i,:] / float(np.sum(self.transition_matrix[i, :]))
        
        while True:
            new_probs = np.dot(probs, norm_transition_matrix)
            diffs = np.abs(probs - new_probs)
            probs = new_probs
            max_diff = np.max(diffs)            
            if max_diff < self.PROB_PRECISION:
                break
        
        return probs
    
    
    def get_transition(self, data):
        return np.random.randint(self.state_count), np.random.randint(self.state_count)        
    
    
    def update(self, data):
        self.data_buffer.append(data)
        if len(self.data_buffer) >= 2:
            transition = self.get_transition((self.data_buffer[-2], self.data_buffer[-1]))
            
            if len(self.data_buffer) > self.window_len:                
                overflow_transition = self.get_transition((self.data_buffer[0], self.data_buffer[1]))                
                self.transition_matrix[overflow_transition] -= 1
                del self.data_buffer[0]
            
            self.transition_matrix[transition] += 1


class RangeMarkovChain(MarkovChain):
    def __init__(self, window_len, state_count):
        MarkovChain.__init__(self, window_len, state_count)
        self.ranges = []        
    
    def get_state(self, value):
        i = 0
        while i < len(self.ranges) and value > self.ranges[i]:
            i += 1
        return i
             
    def get_transition(self, data):
        return (self.get_state(data[0]), self.get_state(data[1]))
            
    def estimate_ranges(self, ranges):
        '''
        Estimate ranges through the percentile method
        '''
        for i in xrange(self.state_count - 1):            
            score = scipy.stats.scoreatpercentile(self.data_buffer, 90 - i*10)
            self.ranges.append(score)
        
    def update(self, data):
        self.data_buffer.append(data)
        if len(self.data_buffer) == self.window_len:
            self.estimate_ranges(self.ranges)
            # calculate the transition matrix
            for i in xrange(len(self.data_buffer)-1):
                transition = self.get_transition((self.data_buffer[i], self.data_buffer[i + 1]))
                self.transition_matrix[transition] += 1
        elif len(self.data_buffer) > self.window_len:                            
            overflow_transition = self.get_transition((self.data_buffer[0], self.data_buffer[1]))
            self.transition_matrix[overflow_transition] -= 1
            transition = self.get_transition((self.data_buffer[-2], self.data_buffer[-1]))
            self.transition_matrix[transition] += 1
            del self.data_buffer[0]


class ReadingFreq(object):
    '''
    Class that holds a counter to each measurement
    '''
    def __init__(self, max_readings=3600):
        self.readings = np.empty(shape=(1, max_readings))
        self.counter = 0
        self.max_readings = max_readings
        self.full = False
    
    def update(self, reading):
        self.readings[0, self.counter] = reading
        self.counter += 1
        if self.counter == self.max_readings:
            self.counter = 0
            self.full = True
    
    def percentile(self, level=90):        
        if not self.full:
            readings = self.readings.view()[0, :self.counter]
        else:
            readings = self.readings
        return np.percentile(readings, level)
            

def main(args):
    if len(args) < 2:
        print "Usage: python %s {trace.arff} -p N -w N -u N" % (args[0])
        exit()
            
    # parameters
    plevel = 90  
    history_window = 7200
    update_interval = 3600
    
    # temps_06_07_12_18h38m00s, temps_16_08_12_16h37m01s
    motes_inlet = (253, 249, 245, 239, 241, 237)    
    
    motes_inlet = map(str, motes_inlet)
            
    filename = args[1]
    
    optlist, arguments = getopt.getopt(args[2:], "f:p:w:u:")
    for opt, val in optlist:
        if opt == "-p":
            plevel = int(val)
        elif opt == '-w':
            history_window = int(val)
        elif opt == '-u':
            update_interval = int(update_interval)
        else:
            raise Exception("Unrecognized option '%s'" % opt)
    
    print "plevel =", plevel
    print "history_window =", history_window
    print "update_interval =", update_interval
        
    motes_to_ignore = []    
    errors = []
    
    rf = ReadingFreq(max_readings=history_window)    
    outfile = open("percentile.txt", "w")
    next_update = 0    
    tr = tracetools.TraceReader(filename, auto_interpolation=False, motes_to_ignore=motes_to_ignore)
    p = 0
    count = 0
    for data in tr.parse():
        # get all readings
        readings = []
        for key, val in data.items():
            if key != "timestamp":
                for m in motes_inlet:
                    if key.endswith(m):
                        readings.append(val)
                        break
                
        max_val = max(readings)        
        rf.update(max_val)
        
        timestamp = data["timestamp"]
        if next_update < timestamp:            
            p = rf.percentile(level=plevel)
            next_update = timestamp + update_interval
        
        if rf.full:                        
            avg_val = float(sum(readings)) / len(readings)
            min_val = min(readings)
            outfile.write("%s %s %s %s %s\n" % (data["timestamp"], min_val, avg_val, max_val, p))            
            errors.append(max_val - p)
            count += 1
            
    outfile.close()
    
    # calc error
    positive_error = float(sum(x ** 2 for x in errors if x > 0)) / count
    negative_error = float(sum(x ** 2 for x in errors if x < 0)) / count
    
    print "MSE positive:", positive_error
    print "MSE negative:", negative_error

if __name__ == '__main__':
    main(sys.argv)