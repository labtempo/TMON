'''
Created on Dec 23, 2012

@author: Giulio
'''
from ts_bitmaps import TimeseriesBitmap
from sax import SAX


class Anomaly(object):
    TOP_BLAME = 5
    
    def __init__(self, anomaly_level, blamed_ts=None):
        self.anomaly_level = anomaly_level
        self.blamed_ts = blamed_ts
    
    def __repr__(self):
        blamed = [e for e in enumerate(self.blamed_ts)]
        blamed.sort(reverse=True, key=lambda e: e[1])
        blamed = [(blame[0], float(blame[1])) for blame in blamed]
        
        return "Anomaly{level=%f, blamed_ts=%s}" % (self.anomaly_level, blamed[:self.TOP_BLAME])

class AnomalyDetector(object):
    '''
    classdocs
    '''
    def __init__(self):
        self.max_value = 0
        self.min_value = float("inf")
        self.apply_count = 0
        self.apply_threshold = 3
    
    def apply(self, x):
        '''
        @return: anomaly level
        '''        
        if x > self.max_value:
            self.max_value = x
        if x < self.min_value:
            self.min_value = x
        
        self.apply_count += 1
                
    def normalize(self, x):
        return (x - self.min_value) / (self.max_value - self.min_value)
    
    def detect(self, x):
        '''
        @return: anomaly object or None
        '''
        anomaly_level = self.apply(x) #@UnusedVariableWarning
        return None


def ExpSmoothDec(func):    
    def wrapper(self, x):
        alpha = 0.2
        self.mu = alpha * x + (1. - alpha) * self.mu
        return func(self, x)
    return wrapper



class CUSUMDetector(AnomalyDetector):
    def __init__(self, anomaly_threshold=0.8, L=0.3, mu=0, alpha=0.2):
        super(CUSUMDetector, self).__init__()
        self.mu = mu
        self.L = L
        self.c = 0
        self.alpha = alpha
        self.anomaly_threshold = anomaly_threshold
        
    def apply(self, x):
        super(CUSUMDetector, self).apply(x)
        if self.apply_count > self.apply_threshold:
            x = self.normalize(x)            
            self.mu = self.alpha * x + (1. - self.alpha) * self.mu            
            self.c = max(0, x - (self.mu + self.L) + self.c)
            return self.c
        return 0
    
    def detect(self, x, spirit_weights=None):
        anomaly_level = self.apply(x)
        if anomaly_level > self.anomaly_threshold:
            self.c = 0
            anomaly = Anomaly(anomaly_level, spirit_weights)
            return anomaly        
        
        
class TSBitmaps(AnomalyDetector):
    def __init__(self, lag_window=8, lead_window=4, anomaly_threshold=0.5, N=1600, n=400, alphabet="abcd", bitmap_level=2):
        super(TSBitmaps, self).__init__()
        self.alphabet = alphabet
        self.lagging_tsb = TimeseriesBitmap(self.alphabet, bitmap_level, lag_window)
        self.leading_tsb = TimeseriesBitmap(self.alphabet, bitmap_level, lead_window)
        self.sax = SAX()
        self.N = N # size of the feature window
        #self.n = n # size of the symbol section
        self.symbols_per_word = self.N / n
        self.data_buffer = []
        self.word_buffer = []
        self.anomaly_threshold = anomaly_threshold
            
    def apply(self, x):
        self.data_buffer.append(x)
        if len(self.data_buffer) == self.N:            
            self.word_buffer.append(self.sax.convert(self.data_buffer, self.alphabet, self.symbols_per_word))
            del self.data_buffer[0]
            if len(self.word_buffer) == self.leading_tsb.window_size:                    
                self.lagging_tsb.update(self.word_buffer[0])
                self.leading_tsb.update(self.word_buffer[-1])
                del self.word_buffer[0]
                return self.lagging_tsb.getAnomalyScore(self.leading_tsb)
        return 0
    
    
    def detect(self, x, spirit_weights=None):
        anomaly_level = self.apply(x)
        if anomaly_level > self.anomaly_threshold:
            return Anomaly(anomaly_level, spirit_weights)
        return None


class SPIRITWeightDetector(AnomalyDetector):
    def __init__(self):
        self.last_order = None
        
    def detect(self, x, spirit_weights):
        if not self.last_order:
            self.last_order = [item[0] for item in sorted((elem for elem in enumerate(spirit_weights)), key=lambda x: x[1])]
            return None
        curr_order = sorted((elem for elem in enumerate(spirit_weights)), key=lambda x: x[1])
        if curr_order != self.last_order:
            return Anomaly(1, spirit_weights)
        return None
    
    
class HOTSAXDetectorBruteForce(AnomalyDetector):
    def __init__(self, N = 800, symbols_per_word = 4, alphabet = "abcd"):
        AnomalyDetector.__init__(self)
        self.N = N
        self.symbols_per_word = symbols_per_word
        self.data_buffer = []
        self.apply_count = N
        self.sax = SAX()
        self.alphabet = alphabet        
    
    def apply(self, x):    
        self.data_buffer.append(x)
        if len(self.data_buffer) == self.N:
            word = self.sax.convert(self.data_buffer, self.alphabet, self.symbols_per_word)
            del self.data_buffer[0]
            
            
            