'''
Created on May 31, 2012

@author: giulio

Slices files
'''
import sys
from SharedLibs.tools import open_file, parse_line

def main(args):
    if len(args) < 3:
        print "Usage: python %s {filename} {start} {end} [-t: range is a timestamp (default is line numbers)]" % (args[0])
        exit()

    filename = args[1]
    timestamp_mode = '-t' in args
    if timestamp_mode:
        range_start = float(args[2])
        range_end = float(args[3])
    else:
        range_start = int(args[2])
        range_end = int(args[3]) 


    f = open_file(filename)
    try:
        line_count = 0
        for line in f:
            if timestamp_mode:
                timestamp, mote_id, counter, temperature = parse_line(line) #@UnusedVariable
                if timestamp > range_end:
                    break
                if timestamp >= range_start:
                    print line,
            else:
                if line_count > range_end:
                    break
                if line_count >= range_start:
                    print line,                
                line_count += 1
    finally:
        if f:
            f.close()

if __name__ == '__main__':
    main(sys.argv)