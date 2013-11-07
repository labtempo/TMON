'''
Created on Dec 4, 2012

@author: giulio
'''
import numpy as np
import sys


def hotelling_t2(sample_avg, n, sigma, mu=0):
    aux = sample_avg - mu
    return n * np.dot(np.dot(np.transpose(aux), np.linalg.inv(sigma)), aux) 


cusum_cache = {}
def cusum(c, x, L, mu=0):
    key = (c, x, L, mu)
    result = cusum_cache.get(key, 0)
    if not result:
        result = max(0, x - (mu + L) + c)
        cusum_cache[key] = result
    return result


class SigmaDetector(object):
    def __init__(self, N=3600):        
        self.N = N
        self.values = []
        
    def apply(self, x):
        self.values.append(x)
        if len(self.values) > self.N:
            del self.values[0]
        stddev = max(np.std(self.values), 0.001)
        return x / stddev


class NaiveControl(object):
    def __init__(self, sigma=3, N=3600):
        self.sigma = sigma
        self.N = N
        self.values = []
    
    def apply(self, x):
        self.values.append(x)
        if len(self.values) > self.N:
            del self.values[0]
        stddev = max(np.std(self.values), 0.001)
        mean = np.average(self.values)
        threshold = self.sigma * stddev
        return bool(not (mean - threshold < x < mean + threshold))


class ExpAvgControl(object):
    def __init__(self, alpha=0.8):
        self.alpha = 0.8
        self.Y = 0
    
    def apply(self, x):
        error = (x - self.Y) ** 2
        self.Y = self.alpha * self.Y + (1. - self.alpha) * x
        return error





class CUSUM(object):    
    def __init__(self, L=0.55, cutoff=250):
        self.c = 0        
        self.mu = 0
        self.L = L
        self.cutoff = cutoff
    
    def apply(self, x):
        self.c = max(0, x - (self.mu + self.L) + self.c)
        result = self.c
        if self.c > self.cutoff:
            self.c = 0
        return result


class MultivarCUSUM(object):
    pass


class ModCUSUM(object):
    def __init__(self, l=1, h=1, N=60):
        # parameters
        self.l = l
        self.h = h
        self.N = N
        
        self.c = 0
        self.mu = 0        
        self.stddev = 0
        self.values = []
    
    def apply(self, x):
        self.values.append(x)
        if len(self.values) > self.N:
            del self.values[0]
        
        # update parameters
        self.stddev = np.std(self.values)
        L = self.l * self.stddev        
        H = max(self.h * self.stddev, 0.001)
        self.mu = np.average(self.values)
        
        self.c = 0
        for value in self.values:
            self.c = cusum(self.c, value, L, self.mu)
        result = self.c
        if result > H:
            self.c = 0
        
        return result
            

def test_hotelling_t2():
    n = 10
    x1 = np.random.normal(size=n)
    x2 = np.random.normal(size=n)
    x3 = np.random.normal(size=n)
    
    x_bar = np.array([np.average(x1), np.average(x2), np.average(x3)])
    sigma = np.cov(np.array([x1, x2, x3]))
    mu = np.zeros(3)
    #mu.fill(0)
    #mu = 0
    print hotelling_t2(x_bar, n, sigma, mu=mu)
    
    
def test_cusum():
    n = 100
    L = 0 # range to ignore
    c = 0
    for x in np.random.normal(size=n):
        c = cusum(c, x, L)
        print "x = %.1f, c = %.1f" % (x, c)


def main(args):
    #test_hotelling_t2()
    #test_cusum()
    timeseries_path = args[1]
    anomalies_path = "cusum_anomalies.txt"
    with open(timeseries_path, "r") as timeseries_f:
        min_value = float("inf")
        max_value = 0.0
        for line in timeseries_f:
            line = line.strip()
            if line:
                value = float(line.split()[1])
                if value < min_value:
                    min_value = value
                if value > max_value:
                    max_value = value
        
        #detector = CUSUM(L=0.55, cutoff=250)
        #detector = ModCUSUM(l=2, h=2, N=1800)
        #detector = SigmaDetector(N=7200)
        #detector = NaiveControl(sigma=2, N=600)
        detector = ExpAvgControl(alpha=0.9)
        timeseries_f.seek(0)
        with open(anomalies_path, "w") as anomalies_f:
            for line in timeseries_f:
                line = line.strip()
                if line:
                    timestamp, value = line.split()
                    value = (float(value) - min_value) / (max_value - min_value)
                    timestamp = float(timestamp)
                    c = detector.apply(value)            
                    anomalies_f.write("%f %f\n" % (timestamp, c))
                    
if __name__ == '__main__':
    main(sys.argv)