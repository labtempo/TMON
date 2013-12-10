'''
Created on May 17, 2012

@author: Giulio

Script that takes a file with readings and compress it using a constant factor.
This factor is translated as the number of lines used to compress (average) over.

Note: the counter information is lost, for obvious reasons. 
'''

import sys, os
from SharedLibs.tracetools import TraceReader, TraceWriter

def main(args):
    if "-h" in args or len(args) < 2:
        print 'Usage: python %s {compression factor} {input file path}' % (args[0])
        exit()
    
    compression_factor = int(args[1])    
        
    input_file_path = args[2]        
    
    motes = {} # holds last reading for each mote
    
    tr = TraceReader(input_file_path)
    tw = TraceWriter("%s_compressed.%s" % (os.path.basename(input_file_path).split(".")[0], tr.file_type), tr.arff_attributes)
    
    try:
        for timestamp, mote_id, counter, temperature in tr.read():            
            mote = motes.get(mote_id, None)
            if mote is not None:
                if len(mote['temp_buffer']) >= compression_factor:
                    avg_temp = sum(mote['temp_buffer']) / len(mote['temp_buffer'])
                    initial_timestamp = mote['timestamp_buffer'][0]
                    
                    tw.write((initial_timestamp, mote_id, avg_temp))
                    
                    del mote['temp_buffer'][:]
                    del mote['timestamp_buffer'][:]
            else:
                motes[mote_id] = {'temp_buffer': [], 'timestamp_buffer': []}
                
            motes[mote_id]['temp_buffer'].append(temperature)
            motes[mote_id]['timestamp_buffer'].append(timestamp)    
    finally:
        tw.close()

if __name__ == '__main__':
    main(sys.argv)
    