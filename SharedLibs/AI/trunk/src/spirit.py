'''
Created on Aug 3, 2012

@author: Giulio
'''
from SharedLibs.tracetools import TraceReader
import numpy as np
import sys

np.set_printoptions(threshold=20) # allows to print big matrixes

ALTERNATIVE_ANOMALY_DETECTION = False
MINIMUM_ANOMALY_LENGTH = 1 * 60 # in seconds
EXTRA_WARNING_INTERVAL = 1 * 60

DEBUG = False
SMALL_POSITIVE_VALUE = 0.01
INIT_TIME = 1 # time to wait before detecting anomalies

# output codes
OC_ANOMALIES   = 2 ** 0
OC_HIDDEN_VARS = 2 ** 1
OC_WEIGHTS     = 2 ** 2
OC_ERRORS      = 2 ** 3
OC_ANOMALIES_2 = 2 ** 4

OUTPUT_MODE = ('Output modes (choose as many as you like): "anomalies": %d, "y": %d (hidden vars), "blame": %d, ' + \
              '"errors": %d, "anomalies_2": %d') % \
              (OC_ANOMALIES, OC_HIDDEN_VARS, OC_WEIGHTS, OC_ERRORS, OC_ANOMALIES_2) 


class Spirit(object):
    def __init__(self, l=0.96, f_E=0.95, F_E=0.98, k=3, hold_off_time=10, fixed_k=False, detect_anomalies=True):
        '''        
        @param n            : number of streams
        @param l            : lambda factor of exponential forgetting, recommended value is 0.96
        @param f_E          : energy threshold to increase the number of hidden vars, recommended 0.95
        @param F_E          : energy threshold to decrease the number of hidden vars, recommended 0.98
        @param k            : initial number of hidden variables, recommended 1
        @param hold_off_time: time window to wait before changing the number of vars again
        @param fixed_k      : don't recalculate the optimal number of hidden vars
        '''
        self.n = 0
        self.k = k
        self.l = l
        self.f_E = f_E
        self.F_E = F_E
        self.t = 1 # track time
        self.EX = 0
        self.EY = 0
        self.hold_off_time = hold_off_time
        self.last_change_at = 1
        self.fixed_k = fixed_k
            
        self.w = new_matrix(shape=(self.n, self.n))
        self.d = new_matrix(shape=(self.n, 1)) # energy proportional to the i-th eigenval of X^T * X
        
        self._resize_matrixes(1) # initial value of n
                
        self.anom_detec_error = 0
        self.detect_anomalies = detect_anomalies
        
    
    def _resize_matrixes(self, n):
        self.w = np.mat(np.resize(self.w, (n, n)))
        self.d = np.mat(np.resize(self.d, (n, 1)))
        
        if n > self.n:
            for i in xrange(max(self.n - 1, 0), n):
                for j in xrange(n):                          
                    self.w[i, j] = 0.
                    self.w[j, i] = 0.
                    if i == j:
                        self.w[i, i] = 1.     
                self.d[i] = SMALL_POSITIVE_VALUE            
        self.n = n
    
    def _trackW(self, x_t, k, w, d, l):        
        y = new_matrix(shape=(k, 1)) # vector of hidden variables        
        x_accute = x_t.copy()
                
        for i in xrange(k):
            y[i] = w[:, i].T * x_accute
            d[i] = l * d[i] + y[i] ** 2            
            e = x_accute - float(y[i]) * w[:, i]
            w[:, i] += float(y[i] / d[i]) * e
            x_accute = x_accute - float(y[i]) * w[:, i]
            w[:, i] = w[:, i] / np.linalg.norm(w[:, i]) # turns it into a unit vector
        
        '''
        Sometimes the QR orthonomalization step changes the signs of the weight matrix.
        @todo: there is no need to do orthonormalization on every step.
        '''
        sign = w[0, 0] > 0
        w[:,:k] = np.linalg.qr(w[:,:k])[0]
        if (w[0, 0] > 0) != sign:
            w[:,:k] = -w[:,:k]
    
    def _anomalyDetection(self, x_t, Y):
        '''
        @return: a positive number on detected anomalies and 0 otherwise
        '''
        # update the estimates        
        self.EX = self.l * self.EX + np.sum(np.power(x_t, 2))
        self.EY = self.l * self.EY + np.sum(np.power(Y, 2))
        
        #print "x_t", self.EX
        
        #print "Y", self.EY
        ratio = self.EY / self.EX
        #print 'ratio', ratio
                
        if self.last_change_at < self.t - self.hold_off_time:
            #print self.k, self.n, self.EY, self.f_E * self.EX
            if self.k < self.n and self.EY < self.f_E * self.EX:
                self.last_change_at = self.t
                #self.k += 1
                print 'up', ratio, self.t
                return 1
                    
            if self.k > 1 and self.EY > self.F_E * self.EX:
                self.last_change_at = self.t
                #self.k -= 1
                print 'down', ratio, self.t                                               
                return 1        
        
        return 0
    
    @staticmethod
    def reconstruct(w, k, Y):
        return w[:, :k] * Y 
    
    
    def update(self, x_t):
        if x_t.shape[0] != self.n:
            self._resize_matrixes(x_t.shape[0])
            self.k = min(self.k, self.n)
            
        self._trackW(x_t, self.k, self.w, self.d, self.l)
        Y = self.w[:,:self.k].T * x_t
                
        if self.detect_anomalies:
            anom = self._anomalyDetection(x_t, Y)
        else:
            anom = 0              
        self.t += 1
        
        return anom, Y
    

class Spirit2(Spirit):
    def _anomalyDetection(self, x_t, Y):
        x_t_prime = self.reconstruct(self.w, self.k, Y)
        
        error = sum( np.abs((x_t[i] - x_t_prime[i]) / x_t[i]) for i in xrange(self.n) ) / self.n
        #print 'error', error
        self.anom_detec_error = error
        
        if error > self.F_E:
            return error
            
        '''
        if self.last_change_at < self.t - self.hold_off_time:            
            if self.k < self.n and error > self.F_E:
                print 'up'
                self.last_change_at = self.t
                self.k += 1               
                return error                    
            if self.k > 1 and error < self.f_E:
                print 'down'
                self.last_change_at = self.t
                self.k -= 1                        
                return error
        '''
        
        return 0


def new_matrix(shape):   
    return np.mat(np.zeros(shape))


def auto_offset(data_buffers, dict_data, aof_window_size):
    data_buffers.append([v for k, v in dict_data.items() if k != "timestamp"])                
    data = data_buffers[-1]                
    if len(data_buffers) > aof_window_size:
        del data_buffers[0]
        data_dim = len(data_buffers[0])
        for i in xrange(data_dim):
            data_offset = float(sum(d[i] for d in data_buffers)) / aof_window_size
            data[i] -= data_offset
    return np.matrix(data).T


def write_header(f, arff_attributes):
    header = " ".join(attribute for attribute in arff_attributes if attribute != 'timestamp')
    f.write("#%s\n" % header)


def main(args):
    if len(args) < 2:
        print ("Usage: python %s {filename} [-et f_E,F_E] [-of (offset for the data)] " + \
               "[-l (lambda)] [-o (output mode)] [-k (fixed k mode)] [-aof (automatic data offset)] " + \
               "[-i (ignore motes)]") % (args[0])
        print OUTPUT_MODE        
        exit()
    
    filename = args[1]
    
    if not filename.endswith(".arff"):
        print "Only arff files are supported"
        exit()
    
    # set parameters
    energy_thresholds = map(float, args[ args.index('-et') + 1: args.index('-et') + 3 ]) if '-et' in args else (0.95, 0.98)
    data_offset = float(args[args.index('-of') + 1]) if '-of' in args else 0
    output_modes = int(args[args.index('-o') + 1]) if '-o' in args else OC_ANOMALIES
    l = float(args[args.index('-l') + 1]) if '-l' in args else 0.96
    fixed_k = int(args[args.index('-k') + 1]) if '-k' in args else 0
    automatic_data_offset = '-aof' in args
    aof_window_size = 200
    motes_to_ignore = args[args.index('-i') + 1:] if '-i' in args else []    
    current_anomaly = []
    extra_warning_counter = 0
    detect_anomalies = output_modes & OC_ANOMALIES
    
    if ALTERNATIVE_ANOMALY_DETECTION:
        spirit_cls = Spirit2
    else:
        spirit_cls = Spirit
        
    s = spirit_cls(l=l, f_E=energy_thresholds[0], F_E=energy_thresholds[1], fixed_k=fixed_k, \
               k=fixed_k if fixed_k else 1, detect_anomalies=detect_anomalies)
           
    # print information
    print "# Info:"
    print "# Number of streams:", s.n
    print "# Lambda:", s.l
    print "# Energy Thresholds:", energy_thresholds
    print "# Offset:", data_offset
    print "# Output modes: %d; %s" % (output_modes, OUTPUT_MODE)
    print "# fixed_k:", fixed_k
    print "# automatic data offset:", automatic_data_offset
               
    anomalies_file = open("anomalies.txt", "w") if detect_anomalies else None    
    hv_file = open("hidden_vars.txt", "w") if output_modes & OC_HIDDEN_VARS else None
    blame_file = open("blame.txt", "w") if output_modes & OC_WEIGHTS else None
    errors_file = open("errors.txt", "w") if output_modes & OC_ERRORS else None
    anomalies_file_2 = open("anomalies_2.txt", "w") if output_modes & OC_ANOMALIES_2 else None
    files = [anomalies_file, hv_file, blame_file, errors_file, anomalies_file_2]
    tr = TraceReader(filename, motes_to_ignore=motes_to_ignore)
    
    
    # write headers
    for f in files:
        if f and f not in (anomalies_file, anomalies_file_2):
            write_header(f, tr.arff_attributes)
    
    
    data_buffers = [] # used of aof
    try:
        for dict_data in tr:
            if automatic_data_offset:
                data = auto_offset(data_buffers, dict_data, aof_window_size)
            else:
                data = np.matrix([v + data_offset for k, v in dict_data.items() if k != "timestamp"]).T
            
            anomaly_level, Y = s.update(data)
            
            if detect_anomalies:
                anomaly_detected = anomaly_level > 0
                if anomaly_detected :
                    if not current_anomaly:
                        current_anomaly.append(dict_data['timestamp'])
                    extra_warning_counter = 0
                elif not anomaly_detected and current_anomaly:
                    extra_warning_counter += 1
                    if extra_warning_counter == EXTRA_WARNING_INTERVAL:                    
                        current_anomaly.append(dict_data['timestamp'])
                        
                        anomaly_length = current_anomaly[1] - current_anomaly[0]                    
                        if anomaly_length > MINIMUM_ANOMALY_LENGTH: 
                            anomalies_file.write(' '.join(str(timestamp) for timestamp in current_anomaly) + "\n")
                        del current_anomaly[:]
                        extra_warning_counter = 0
                        
                if anomalies_file_2:
                    anomalies_file_2.write("%f %f\n" % (dict_data['timestamp'], s.anom_detec_error))                
                            
                            
            if blame_file:                
                blame_file.write("%f %s\n" % (dict_data["timestamp"], " ".join("%f" % w for w in s.w[:,s.k - 1])))
                    
            if hv_file:
                hv_file.write("%f %s\n" % (dict_data["timestamp"], " ".join("%f" % y for y in Y)))
            
            if errors_file:                
                reconstructed_x = s.reconstruct(s.w, k, Y)                                
                errors_file.write("%f %s\n"% (dict_data["timestamp"], \
                                              " ".join(str(float(data[i] - reconstructed_x[i])) for i in xrange(len(data)))))
    finally:
        for f in files:
            if f:
                f.close()
    
    
if __name__ == '__main__':
    main(sys.argv)
    #main(['', r'D:\Giulio\My Dropbox\Projeto Sensores\experiments\falta_de_luz\energy_saving\cut3\cut.arff', '-k', '1', \
    #      '-et', '0.9999', '0.999'])
    
    
    