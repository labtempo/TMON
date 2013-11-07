'''
Created on May 16, 2012

@author: Giulio

A script that fills missing data between readings. For instance, if a input file
looks like this:

<timestamp> <node_id> <counter> <temp>
...
123333335.6 12        36        27.889
123333336.6 12        37        28.889
123333338.6 12        38        27.889
...

This script will fill the blank instant 123333336.7 with previous data:

<timestamp> <node_id> <counter> <temp>
...
123333335.6 12        36        27.889
123333336.6 12        37        28.889
123333336.7 12        37        28.889 <<<
123333338.6 12        38        27.889
...

Rationale:
    Many energy saving algorithms works with redundant data suppression. 
    However, many data mining algorithms (e.g. SAX) works with evenly 
    spaced time-series. Thus, there's a need to generate these kind of 
    files.

Note:
    Redundant data suppression (at the time of this writing) and lost
    messages are completely indistinguishable.
'''

import sys
from SharedLibs.tools import open_file, parse_line

TIME_RESOLUTION = 1.0 # seconds that are expected between two consecutive messages
MAX_TIME_DELTA = 0.8 * TIME_RESOLUTION # maximum time plus overhead

def main(args):
    if len(args) < 2:
        print 'Usage: python %s {input file path}' % (args[0])
        exit()
    
    input_file_path = args[1]
    output_file_path = "%s.filled.gz" % (input_file_path)
    #output_file_path = "%s.filled" % (input_file_path)
    
    input_file = open_file(input_file_path, 'r')
    output_file = open_file(output_file_path, "w")
    try:
        motes = {} # holds last reading for each mote
        
        for line in input_file:
            timestamp, mote_id, counter, temperature = parse_line(line)
            mote = motes.get(mote_id, None)
            if mote is not None:
                prev_timestamp,  prev_line = mote
                
                if timestamp < prev_timestamp:
                    print "Timestamps out of order: %f > %f" % (prev_timestamp, timestamp)
                    exit()

                time_delta = timestamp - (prev_timestamp + TIME_RESOLUTION)
                
                while time_delta > MAX_TIME_DELTA:
                    # needs to fill data
                    prev_timestamp += TIME_RESOLUTION
                    time_delta -= TIME_RESOLUTION
                    output_file.write("%f %s" % (prev_timestamp, prev_line))
                    
            motes[mote_id] = (timestamp, line[line.index(" ") + 1:]) # line minus the timestamp
            
            # writes original data
            output_file.write(line)
                
    finally:
        if input_file:
            input_file.close()
        if output_file:
            output_file.close()

if __name__ == '__main__':
    main(sys.argv)
    #main(['readings_filler','../tests/filler_test1.txt'])
    