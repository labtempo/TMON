'''
Created on Nov 6, 2012

@author: giulio
'''
import sys

from SharedLibs.tools import execCmd
import time

FETCH_CMD = "rrdtool fetch %s %s %s"

def fetch(filename, CF="AVERAGE", start=None, end=None):
    options = []
    if start:
        options.append("--start %s" % (start))
    if end:
        options.append("--end %s" % (end))
    
    cmd = FETCH_CMD % (filename, CF, " ".join(options))
    return execCmd(cmd.split())


def parse_fetch(text):
    for line in text.splitlines():
        tokens = line.split(": ")
        if len(tokens) == 2 and not tokens[1].endswith('nan'):            
            yield float(tokens[0]), float(tokens[1])


def enrich_arff(arff_filename, output_filename, rrd_filename, header):
    # get first and last timestamp of the arrf_file
    timestamp_start = 0
    timestamp_end = 0
    
    with open(arff_filename, "r") as f:
        # advance to data
        while True:
            line = f.readline()
            if line.startswith("@data"):
                break
        
        line = f.readline()
        tokens = line.split(",")
        timestamp_start = int(float(tokens[0]))
        
        f.seek(-512, 2) # go to somewhere near the last line
        # advance to last line
        for line in f:
            pass
        tokens = line.split(",")
        timestamp_end = int(float(tokens[0]))
    
    assert timestamp_start < timestamp_end
    
    arff_header = []
    
    with open(output_filename, "w") as out_f:
        with open(arff_filename, "r") as arff_f:
            while True:
                line = arff_f.readline()                
                if line.startswith("@data"):
                    break
                arff_header.append(line)
            
            arff_header.append(header)
            arff_header.append(line)                        
            
            arff_header = "".join(arff_header)
            out_f.write(arff_header)
        
            i = 0
            rrd_data = [data for data in parse_fetch(fetch(rrd_filename, start=str(timestamp_start), end=str(timestamp_end)))]
            if not rrd_data:
                print "Nothing found on interval: %s (%s) -- %s (%s)" % (timestamp_start, time.ctime(timestamp_start), \
                                                                         timestamp_end, time.ctime(timestamp_end))
                return
            
            for line in arff_f:
                if line:
                    curr_timestamp = float(line.split(",")[0])                
                    while i + 1 < len(rrd_data) and curr_timestamp > rrd_data[i][0]:
                        i += 1
                        # print progress here
                        print "Time left: %00000000d s" % (timestamp_end - curr_timestamp)                    
                    line = "%s,%s\n" % (line[:-1], rrd_data[i][1])
                out_f.write(line)
                    

def main(args):
    fetch_output = fetch('/home/giulio/ganglia/uff/uff22/cpu_idle.rrd', start='-1d', end="")
    for s in parse_fetch(fetch_output):
        print time.ctime(s[0]), s[1]
    enrich_arff("/home/giulio/workspace/MultihopCollectorSensingLpl/trunk/output/samples_23_10_12_16h55m54s.arff", \
                "out.arff", '/home/giulio/ganglia/uff/uff21/cpu_idle.rrd', "@attribute uff_21_cpu_idle numeric")

if __name__ == '__main__':
    main(sys.argv)