'''
Created on Apr 8, 2013

@author: giulio
'''
import sys
from SharedLibs.tracetools import TraceReader, TraceAdapter, UNIFORM_FILE_FORMAT, TraceWriter
from collections import OrderedDict


class Sensor(object):
    DELTA = 0.5
    MAX_SEND_INTERVAL = 30 * 60
    
    def __init__(self):
        self.last_temp = -1
        self.time_since_last_send = 0
    
    def emulate(self, temp):
        if self.time_since_last_send > self.MAX_SEND_INTERVAL:
            self.time_since_last_send = 0
            self.last_temp = temp
            return temp
        
        if abs(self.last_temp - temp) > self.DELTA:
            self.time_since_last_send = 0
            self.last_temp = temp                        
            return temp
        
        self.time_since_last_send += 1
        
        return self.last_temp


def main(args):
    if len(args) < 2:
        print "Usage: python %s {filename} [-compress {factor}]"
        exit()
    
    filename = args[1]
    compression_factor = int(args[3]) if len(args) > 2 else 1
    tr = TraceReader(filename)
    tw = TraceWriter('output.arff', tr.arff_attributes)
            
    sensors = None
    data_keys = None
    data_keys_len = 0
    out_data = OrderedDict()    
    count = 1
    
    for data in tr.parse():                
        if not sensors:
            sensors = [Sensor() for _i in xrange(len(data) - 1)]
            data_keys = data.keys()
            data_keys_len = len(data_keys)
            for key in data_keys:
                out_data[key] = 0.0
        
        for i in xrange(1, data_keys_len):
            key = data_keys[i]
            out_data[key] += sensors[i - 1].emulate(data[key])
                
        if count % compression_factor == 0:
            out_data['timestamp'] = data['timestamp'] - compression_factor / 2.
                        
            for i in xrange(1, data_keys_len):
                out_data[data_keys[i]] /= compression_factor
            
            tw.write(out_data)
            
            for key in data_keys:
                out_data[key] = 0.0
        
        count += 1
    
    tw.close()
    
if __name__ == '__main__':
    main(sys.argv)