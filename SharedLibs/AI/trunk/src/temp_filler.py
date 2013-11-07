'''
Created on Feb 25, 2013

@author: giulio

Fill temperature values from the start and end of the trace.
'''
import sys
from SharedLibs.tracetools import TraceReader


def main(args):
    filename = '/home/giulio/Dropbox/Projeto Sensores/experiments/temperatura/sala_servidores/samples_20_02_13_15h05m47s.agg'
    motes_to_ignore = []
    tr = TraceReader(filename, motes_to_ignore)
    
    mote_first_data = {}
    mote_last_data = {}
    line_count = 0
    
    for data in tr.read():
        mote_id = data[1]
        if mote_id not in mote_first_data.iterkeys():
            mote_first_data[mote_id] = data
        mote_last_data[mote_id] = data
        line_count += 1
    
    tr.reset()
    
    # replicate all the first temps to the smallest timestamp
    min_timestamp = min(data[0] for data in mote_first_data.itervalues())
        
    for data in mote_first_data.itervalues():
        if data[0] != min_timestamp:
            data = list(data)
            data[0] = min_timestamp
            print " ".join(str(d) for d in data)
    
    # print all data except last line
    for data in tr.read():
        print " ".join(str(d) for d in data)
        line_count -= 1
        if line_count == 1:
            break
    
    max_timestamp = max(data[0] for data in mote_last_data.itervalues())
    
    for data in mote_last_data.itervalues():
        if data[0] != max_timestamp:
            data = list(data)
            data[0] = max_timestamp
            print " ".join(str(d) for d in data)

if __name__ == '__main__':
    main(sys.argv)