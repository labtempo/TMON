'''
Created on May 29, 2012

@author: giulio

Script that outputs the maximum common interval among a set of motes that
respects a maximum latency threshold.
'''

import sys
from SharedLibs.tools import open_file, parse_line

INFINITY = float('inf')


def read_intervals(input_filename, motes_to_ignore, max_latency):
    motes = {}
    
    if not input_filename:
        f = sys.stdin
        if f.closed:
            return motes        
    else:
        f = open_file(input_filename, "r")
    
    try:
        for line in f:
            timestamp, mote_id, counter, temperature = parse_line(line)
            if mote_id not in motes_to_ignore:            
                mote = motes.get(mote_id, None)
                if mote is None:
                    motes[mote_id] = [ [timestamp, timestamp] ]
                
                if motes[mote_id][-1][1] - motes[mote_id][-1][0] > max_latency:
                    '''
                    Close the interval
                    '''
                    motes[mote_id].append( [timestamp, timestamp] )
                else:
                    '''
                    Update the end of the last interval
                    '''
                    motes[mote_id][-1][1] = timestamp
    finally:
        if f:
            f.close()
    
    find_small_intervals(motes)
    
    return motes.values()


def find_small_intervals(motes):
    if not motes:
        return
    
    average_length = 0.0
    avgs = {}
    for mote_id, intervals in motes.items():
        avg = sum((interval[1] - interval[0] for interval in intervals)) / len(intervals)
        average_length += avg
        avgs[mote_id] = avg
    average_length /= len(motes)
    
    for mote_id, avg in avgs.items():
        if avg < average_length * 0.8:
            print "Warning! Mote %d is too small" % (mote_id)        


def intersect(interval_a, interval_b):
    if interval_a[0] <= interval_b[0] <= interval_a[1]:
        return (interval_b[0], min(interval_a[1], interval_b[1]))
    
    if interval_b[0] <= interval_a[0] <= interval_b[1]:
        return (interval_a[0], min(interval_b[1], interval_a[1]))
        
    return None


def greatest_intersection(interval, intervals_to_check, row=0, largest_len=0):    
    greatest = (0, 0)
    
    if row < len(intervals_to_check):
        for j in range(len(intervals_to_check[row])):
            next_interval = intervals_to_check[row][j]
            
            if interval[1] <= next_interval[0] or next_interval[1] - next_interval[0] < largest_len:        
                break
            
            gi = intersect(interval, greatest_intersection(next_interval, intervals_to_check, row=row+1, largest_len=largest_len))        
            if gi and gi[1] - gi[0] >= greatest[1] - greatest[0]:
                greatest = gi
                if largest_len < greatest[1] - greatest[0]:
                    largest_len = greatest[1] - greatest[0]
    else:
        return interval
    
    return greatest


def main(args):
    
    if len(args) < 2 or '-h' in args:
        print "Usage: python %s {max latency} [-f input filename (default is stdin)] [-i ignore-list]" % (args[0])
        exit()

    motes_to_ignore = []
    if '-i' in args:
        motes_to_ignore = map(int, args[args.index('-i') + 1].split(',') )

    input_filename = None
    if '-f' in args:    
        input_filename = args[args.index('-f') + 1]
        
    max_latency = float(args[1])
            
    '''
    Construct intervals
    '''
    print "Reading intervals...",
    motes_intervals = read_intervals(input_filename, motes_to_ignore, max_latency)
    print " found %d intervals" % sum( ( len(i) for i in motes_intervals ) )
    
    if not motes_intervals:
        exit()
    
    # heuristic
    motes_intervals.sort(key=lambda m: sum([b - a for a, b in m]), reverse=True)
            
    '''
    Obtain the greatest intersection
    '''
    print "Calculating longest intersection..."
    longest_start = 0
    longest_end = 0
    count = 0
    for i in motes_intervals[0]:
        count += 1
        gi = greatest_intersection(i, motes_intervals)
        if gi[1] - gi[0] > longest_end - longest_start:
            longest_start = gi[0]
            longest_end = gi[1]
       
       
    print "Maximum Common Interval: %f to %f (%f seconds)" % (longest_start, longest_end, longest_end - longest_start)
    return longest_start, longest_end
    
        
if __name__ == '__main__':
    main(sys.argv)