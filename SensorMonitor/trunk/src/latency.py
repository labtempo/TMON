'''
Created on May 29, 2012

@author: giulio

Script that outputs latencies for each mote on file
'''

import sys
import numpy
from SharedLibs.tools import parse_line, open_file


def read_latencies(input_filename, discard=20*60):
    '''
    @param discard: number of seconds to discard out of the experiment beginning 
    '''
    motes = {}
    
    discard_time = 0
    f = open_file(input_filename)
    
    try:
        for line in f:
            timestamp, mote_id, counter, temperature = parse_line(line)
            if not discard_time:
                discard_time = timestamp + discard
            
            if timestamp >= discard_time:                
                mote = motes.get(mote_id, None)
                if mote is None:
                    mote = {"last_timestamp": timestamp, "latencies": []}
                    motes[mote_id] = mote
                else:
                    latency = timestamp - mote["last_timestamp"]
                    mote["latencies"].append(latency)                
                
                mote["last_timestamp"] = timestamp
    finally:
        if f:
            f.close()

    
    return motes


def main(args):
    
    if len(args) < 2:
        print "Usage: python %s {input filename}"
        exit()

    input_filename = args[1]
    
    motes = read_latencies(input_filename)

    for mote_id, mote in motes.items():            
        latencies = mote["latencies"]
        max_latency = numpy.max(latencies)
        min_latency = numpy.min(latencies)
        avg_latency = numpy.mean(latencies)
        std_dev_latency = numpy.std(latencies)
        print "Mote %2d -- min: %-9.5f, mean: %-9.5f, max: %-9.5f, std_dev: %-9.5f" % \
                (mote_id, min_latency, avg_latency, max_latency, std_dev_latency)
   
if __name__ == '__main__':
    main(sys.argv)