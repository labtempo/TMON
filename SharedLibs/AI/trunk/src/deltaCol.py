'''
Script that calculates the delta (first derivative) of column-based file.

E.g.
120 2 26
121 2 27
122 3 25
124 3 29

Output:
1 2 1
2 3 2
'''
import sys
from SharedLibs.tools import parse_line, open_file

def main(args):
    if "-h" in args:
        print "python %s [input filename]  [-s (suppress zero temperature diffs)] [-j (join zero temperature diffs)]" % (args[0])
        exit()
    
    suppress_zero_diff = '-s' in args
    if suppress_zero_diff:
        args.remove('-s')
    
    join_zero_temperature_diffs = '-j' in args
    if join_zero_temperature_diffs:
        args.remove('-j')
    
    f = sys.stdin
    if len(args) > 1:
        f = open_file(args[1])
    motes = {}
    diff_temp = -1.0
    try:
        for line in f:
            timestamp, mote_id, counter, temperature = parse_line(line)
            
            mote = motes.get(mote_id, None)
            if not mote:
                motes[mote_id] = mote = {}
            else:
                diff_timestamp = timestamp - mote['ts']
                diff_temp = temperature - mote['temp']
                if diff_timestamp > 0.00000001 and (not suppress_zero_diff or diff_temp != 0.0):
                    print diff_timestamp, mote_id, diff_temp / diff_timestamp
            if not join_zero_temperature_diffs or (diff_temp != 0.0):
                mote['ts'] = timestamp
                mote['temp'] = temperature 
    finally:
        if f:
            f.close()

if __name__ == "__main__":
    main(sys.argv)