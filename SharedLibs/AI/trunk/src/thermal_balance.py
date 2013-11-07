'''
Plot temperatures of multiple motes
'''
import datetime
import sys
from collections import OrderedDict

from SharedLibs.tools import open_file, parse_line, read_file

MAX_COUNTER = 2**16 - 1

try:
    import pylab
except ImportError:
    print "You must install pylab if you intend to plot stuff"
    exit()
try:
    import matplotlib
except ImportError:
    print "You must install matplotlib if you intend to plot stuff"
    exit()


def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return v, v, v
    i = int(h*6.0) # XXX assume int() truncates!
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q
    raise Exception("WOW!")


class TimeSeries(object):
    def __init__(self):
        self.data = OrderedDict() # sort by timestamp
        
    def merge(self, value1, value2):
        merged = []
        for item1, item2 in zip(value1, value2):
            if item1 is None:
                merged.append(item2)
            else:
                merged.append(item1)
        return tuple(merged)
    
    def add(self, timestamp, value):
        pre_value = self.data.get(timestamp, None)
        if pre_value is None:
            self.data[timestamp] = value
        else:
            self.data[timestamp] = self.merge(pre_value, value)
    
    def iter_column(self, col, value):
        for t, item in self.data.items():            
            if item[col] == value:
                yield t, item
    
    def __iter__(self):
        for t, item in self.data.items():
            yield t, item
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __setitem__(self, index, value):
        self.data[index] = value
        


class Readings(object):
    def __init__(self):
        self.temps = []
        self.counters = []
        self.timestamps = []
    
    def clear(self):
        del self.temps[:]
        del self.counters[:]
        del self.timestamps[:]


class Mote(object):
    def __init__(self, mote_id):
        self.mote_id = mote_id
        self.readings = Readings()    
        self.losses = []
        self.reading_counter = 0
    
    def _add_reading(self, timestamp, temp, counter):        
        self.readings.counters.append(counter)
        self.readings.temps.append(temp)
        self.readings.timestamps.append(timestamp)        
    
    def add_reading(self, timestamp, temp, counter):        
        if len(self.readings.timestamps) > 0 and not (counter is None):            
            expected = self.readings.counters[-1] + 1
            if expected > MAX_COUNTER and counter < MAX_COUNTER / 2:
                expected %= MAX_COUNTER
            self.losses += [timestamp] * int(max(counter - expected, 0))
        self._add_reading(timestamp, temp, counter)
        self.reading_counter += 1
    
    def __repr__(self):
        percent_lost = 0.0
        if self.reading_counter > 0:
            percent_lost = float(len(self.losses) * 100) / (len(self.losses) + self.reading_counter)
            
        if len(self.readings.temps) > 0:
            avg_temp = sum(self.readings.temps) / len(self.readings.temps)
        else:
            avg_temp = 0.0
        return "%s(id=%s, avg(readings)=%f, losses=%d (%f%%))" % (type(self).__name__, self.mote_id, avg_temp, 
                                                                                 len(self.losses), percent_lost)


RACK1, RACK2 = range(1, 3)
VERTICAL_TOP, VERTICAL_CENTER, VERTICAL_BOTTOM = range(3)
HORIZONTAL_LEFT, HORIZONTAL_CENTER, HORIZONTAL_RIGHT = range(3)
FACING_BACK, FACING_LEFT, FACING_RIGHT, FACING_FRONT = range(0, 8, 2)

MOTE_LOCATION = {214: {"rack": RACK2, "facing": FACING_BACK, "horizontal": HORIZONTAL_RIGHT, "vertical": VERTICAL_CENTER}, \
                 216: {"rack": RACK2, "facing": FACING_BACK, "horizontal": HORIZONTAL_LEFT, "vertical": VERTICAL_TOP}, \
                 217: {"rack": RACK2, "facing": FACING_BACK, "horizontal": HORIZONTAL_RIGHT, "vertical": VERTICAL_BOTTOM}, \
                 226: {"rack": RACK2, "facing": FACING_BACK, "horizontal": HORIZONTAL_LEFT, "vertical": VERTICAL_CENTER}, \
                 227: {"rack": RACK2, "facing": FACING_BACK, "horizontal": HORIZONTAL_RIGHT, "vertical": VERTICAL_CENTER}, \
                 237: {"rack": RACK2, "facing": FACING_FRONT, "horizontal": HORIZONTAL_LEFT, "vertical": VERTICAL_CENTER}, \
                 238: {"rack": RACK2, "facing": FACING_BACK, "horizontal": HORIZONTAL_RIGHT, "vertical": VERTICAL_TOP}, \
                 239: {"rack": RACK2, "facing": FACING_FRONT, "horizontal": HORIZONTAL_LEFT, "vertical": VERTICAL_BOTTOM}, \
                 241: {"rack": RACK2, "facing": FACING_FRONT, "horizontal": HORIZONTAL_LEFT, "vertical": VERTICAL_TOP}, \
                }

def is_opposed(mote1, mote2):
    mote1_info = MOTE_LOCATION.get(mote1, None)
    mote2_info = MOTE_LOCATION.get(mote2, None)
    
    if not (mote1_info and mote2_info):
        return False 
    
    return mote1_info['rack'] == mote2_info['rack'] and \
        (mote1_info['facing'] | mote2_info['facing'] == FACING_BACK | FACING_FRONT) and \
         mote1_info['vertical'] == mote2_info['vertical']

   
def mote_diffs(ts, mote1, mote2):
    diff_ts = TimeSeries()
    
    mote1_value = None
    mote2_value = None
    
    for t, data in ts:        
        if data[0] in [mote1, mote2]:
            if data[0] == mote1:
                mote1_value = data[1]
            elif data[0] == mote2:
                mote2_value = data[1]
            if mote1_value is not None and mote2_value is not None:                
                diff_ts.add(t, (mote1_value - mote2_value))
        
    return diff_ts
    

def main(args):    
    if len(args) < 2:
        print "Usage: python %s {input filename} [-f (function to plot with file) mote_id]" % (args[0])
        exit()
    
    filename = args[1]
    ts = TimeSeries()
    motes = set()
    
    print "Parsing..."
    
    f = None    
    file_contents = read_file(filename)
    if not file_contents:
        f = open_file(filename)
        lines_iter = iter(f)
    else:
        lines_iter = iter(file_contents)
    try:
        for line in lines_iter:
            timestamp, mote_id, counter, temp = parse_line(line)
            ts.add(timestamp, (mote_id, temp))
            motes.add(mote_id)
    finally:
        if f:
            f.close()
        if file_contents:
            del file_contents
    
    diffs = []
    for mote_id1 in motes:
        for mote_id2 in motes:
            if mote_id1 < mote_id2 and is_opposed(mote_id1, mote_id2):     
                diff_ts = mote_diffs(ts, mote_id1, mote_id2)
                diffs.append(( "%d-%d (rack %s)" % (mote_id1, mote_id2, MOTE_LOCATION[mote_id1]['rack']), diff_ts))
            
    print "Plotting..."
    
    fig = pylab.figure()    
    pylab.grid(True)
    ax1 = fig.add_subplot(111)
    
    i = 0
    for diff in diffs:
        temps = []
        dates = []        
        for t, temp in diff[1]:
            dates.append(datetime.datetime.fromtimestamp(t))               
            temps.append(temp)
                
        dates = matplotlib.dates.date2num(dates)
        
        h = float(i + 1) / len(diffs)
        color = hsv_to_rgb(h, 0.8, 0.8)
             
        # 'b' means default (plot with lines)
        ax1.plot_date(dates, temps, 'b', color=color)
        i += 1

    pylab.legend( [mote_legend for mote_legend, diff_ts in diffs] )
    
    ax1.set_ylabel("Temp difference (C)")
    ax1.set_xlabel("Time")   
    
    pylab.show()
    
    #fig.savefig('exp.eps')

if __name__ == "__main__":    
    main(sys.argv)