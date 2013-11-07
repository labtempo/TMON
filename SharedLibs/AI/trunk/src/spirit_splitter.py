'''
Created on Dec 26, 2012

@author: Giulio
'''
import numpy as np
from anomaly_detector import CUSUMDetector, TSBitmaps
from SharedLibs.tracetools import TraceReader 
import spirit


class SPIRITSplitter(object):
    def __init__(self, detectors):
        self.spirit = spirit.Spirit(l=1., k=len(detectors), fixed_k=True)
        self.detectors = detectors
        
    def update(self, dict_data):
        data = np.matrix([v for k, v in dict_data.items() if k != "timestamp"]).T
        _, w, Y = self.spirit.update(data)
        #print "Y:"
        ##print Y
        anomalies = []
        for i in xrange(len(self.detectors)):
            detector = self.detectors[i]            
            anomaly = detector.detect(Y[i, 0], w[:, i])
            if anomaly:
                anomalies.append((i, anomaly))
        
        return anomalies
    

def main():
    filename = r"D:\Giulio\My Dropbox\Projeto Sensores\experiments\temperatura\sala_servidores\samples_04_10_12_12h28m36s.arff"
    #filename = r"D:\Giulio\workspace2\SensorMonitor\output\arff\temps_25_05_12_15h09m48s.arff"    
    splits = 1
    
    #detectors = [CUSUMDetector(anomaly_threshold=0.01, L=0.0, alpha=0.6) for _ in xrange(splits)]    
    detectors = [TSBitmaps(lag_window=8, lead_window=8, anomaly_threshold=0.355, N=400, n=100, alphabet="abcd") for _ in xrange(splits)]
    splitter = SPIRITSplitter(detectors)
    
    tr = TraceReader(filename, supress_repetitions=False, auto_timestamps=False, suppress_rapid_changes=False)
    for data in tr.read():
        anomalies = splitter.update(data)
        if anomalies:
            print data['timestamp'] - 600, data['timestamp'] + 600#, anomalies


if __name__ == '__main__':
    main()