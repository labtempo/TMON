'''
Plot temperatures of multiple motes
'''
import datetime
import sys, time
import pprint
import numpy as np
from SharedLibs import tracetools
import math

MAX_COUNTER = 2**16 - 1

try:
    import matplotlib
    matplotlib.use('QT4Agg')
    from matplotlib import pyplot
except ImportError:
    print "You must install matplotlib if you intend to plot stuff"    
    exit()

HIGHLIGHT_COLOR = "#DDDD00"


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

    
class Mote(object):
    def __init__(self, mote_id):
        self.mote_id = mote_id
        self.temps = []
        self.timestamps = []        
    
    def add_reading(self, timestamp, temp):
        self.temps.append(temp)         
        self.timestamps.append(timestamp)
            
    def __repr__(self):            
        if len(self.temps) > 0:
            avg_temp = np.average(self.temps)
        else:
            avg_temp = 0.0
        first_timestamp = int(self.timestamps[0]) if len(self.timestamps) else "---"
        end_timestamp = int(self.timestamps[-1]) if len(self.timestamps) else "---"
        return "%s(id=%s, start=%s, end=%s, avg(readings)=%f, len(readings)=%d)" % \
            (type(self).__name__, self.mote_id, first_timestamp, end_timestamp, avg_temp, len(self.timestamps))
    

def parse(filename, motes, selected_attr, custom_func=None, motes_to_ignore=[]):        
    tr = tracetools.TraceReader(filename, auto_timestamps=True, suppress_rapid_changes=True, \
                                motes_to_ignore=motes_to_ignore)
    if custom_func and tr.file_type != "arff":
        raise Exception("Expected arff file when using a custom_func")
    
    if tr.file_type == "arff":
        for attr in tr.arff_attributes:
            if attr != "timestamp":
                mote_id = attr
                mote = Mote(mote_id)
                motes[mote_id] = mote
           
        for line in tr.parse():
            timestamp = line['timestamp']
            for mote_id, v in line.items()[1:]:                
                motes[mote_id].add_reading(timestamp, v)
    else:
        # agg -> txt        
        if tr.file_type == "agg":
            adapter = tracetools.TraceAdapter(tr, tracetools.RAW_FILE_FORMAT, selected_attr)
            parser_gen = adapter.parse()
        else:
            parser_gen = tr.parse()
        
        for timestamp, mote_id, _counter, value in parser_gen:        
            mote = motes.get(mote_id, None)
            if not mote:                
                mote = Mote(mote_id)
                motes[mote_id] = mote            
            mote.add_reading(timestamp, value)        
            
    # make all keys integers
    for key in motes.keys():
        original_key = key
        if isinstance(key, str):
            tokens = key.split("_")
            if len(tokens) > 1:
                key = int(tokens[1])
            else:
                key = int(key)
            motes[key] = motes[original_key]
            del motes[original_key]


def plot(ax, motes, highlight_filename=None, custom_func_mote=None, custom_func=None, color_code_filename=None):
    pyplot.grid(True)
    pyplot.xticks(rotation=25)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d-%H:%M'))
        
    for mote_id, mote in motes.iteritems():
        temps = mote.temps
        #dates = mote.timestamps
        dates = matplotlib.dates.date2num([datetime.datetime.fromtimestamp(t) for t in mote.timestamps])
                
        h = (mote_id ** 3 % 255) / 255.
        s = 0.8
        v = 0.8
        color = hsv_to_rgb(h, s, v)
        
        # 'b' means default (plot with lines) 
        #ax1.plot(dates, temps, 'b', color=color)
        ax.plot_date(dates, temps, '.-', markersize=5, color=color)        
        if custom_func and mote_id == custom_func_mote:            
            ax.plot(dates, (custom_func(motes, i) for i in range(len(dates))), 'b', color="black")
    
    if highlight_filename:
        try:
            highlight_file = open(highlight_filename)
        except IOError:
            print "WARNING: unable to open highlight file!"
        else:
            try:
                for line in highlight_file:
                    tokens = line.split()
                    start = datetime.datetime.fromtimestamp(float(tokens[0]))
                    #end = datetime.datetime.fromtimestamp(float(tokens[0]) + float(tokens[1]))
                    end = datetime.datetime.fromtimestamp(float(tokens[1]))
                    matplotlib.pyplot.axvspan(start, end, facecolor='r', alpha=0.2)
            finally:
                if highlight_file:
                    highlight_file.close()
    
    if color_code_filename:        
        with open(color_code_filename) as f:
            interval = []
            levels = []                        
            for line in f:
                tokens = line.split()
                timestamp, level = map(float, tokens)
                timestamp = matplotlib.dates.date2num(datetime.datetime.fromtimestamp(timestamp))                
                interval.append(timestamp)
                levels.append(level)
                
                if len(interval) == 2:
                    if levels[0] < 0.2:
                        color = None
                    else:
                        color = hsv_to_rgb(0, min(1, levels[0]), 1)
                    if color:
                        matplotlib.pyplot.axvspan(interval[0], interval[1], facecolor=color, alpha=0.4, edgecolor='white')
                    del interval[0]
                    del levels[0]
                
    
    ax.set_xlabel("Time (day-hours:minutes)")
    pyplot.legend(motes.keys(), loc='center left', bbox_to_anchor=(1.01, 0.5))
    

def parse_regions(regions_filename):
    '''
    Format:
    <region_name> <motes>
    '''
    regions = {}
    with open(regions_filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                tokens = line.split()
                assert len(tokens) >= 2
                regions[tokens[0]] = map(int, tokens[1:])
    return regions


def get_grid_size(graph_count):
    x = y = int(math.ceil(math.sqrt(graph_count)))
    
    while (y - 1) * x >= graph_count:
        y -= 1
    
    return x, y
    


def main(args):    
    if len(args) < 2:        
        usage_str = "Usage: python %s {input filename} [-h (highlight file)] [-i (motes to ignore)] " + \
               "[-f (function to plot with file) mote_id] [-bench (use this to prevent plotting at the end)] " + \
               "[-a {number} (select the attribute)] [-only (motes to plot)] [-regions {regions filename}]"
        print usage_str % (args[0])
                
        exit()
    
    # ARG PARSING
    filename = args[1]
    motes = {}
    
    highlight_mode = '-h' in args
    highlight_filename = args[args.index('-h') + 1] if highlight_mode else None
    
    color_code_mode = '-c' in args
    color_code_filename = args[args.index('-c') + 1] if color_code_mode else None
    
    motes_to_ignore = map(int, args[args.index('-i') + 1:]) if '-i' in args else []    
    motes_to_include = map(int, args[args.index('-only') + 1].split("-")) if '-only' in args else []
        
    custom_func = None
    custom_func_mote = None
    if '-f' in args:
        f = open(args[args.index('-f') + 1])
        try:
            custom_func = eval(f.read())
        finally:
            if f:
                f.close()
        custom_func_mote = int(args[args.index('-f') + 2])
    
    attr_selection = tracetools.TEMP if not "-a" in args else int(args[args.index("-a") + 1])
    
    regions = parse_regions(args[args.index('-regions') + 1]) if '-regions' in args else None
    
    print "Parsing..."
    t0 = time.time()
    parse(filename, motes, attr_selection, custom_func, motes_to_ignore=motes_to_ignore)
        
    if motes_to_include:
        for mote_id in motes.keys():            
            if not mote_id in motes_to_include:
                del motes[mote_id]
      
    pprint.pprint(motes)
    t1 = time.time()    
    print "Took %2.0f seconds to parse." % (t1 - t0)
        
    print "Plotting..."
    fig = pyplot.figure()
    
    if regions: 
        grid_size_x, grid_size_y = get_grid_size(len(regions.keys()))
        position = 1
        for region_name, region_motes in regions.iteritems():
            filtered_motes = {}
            for mote_key, mote_item in motes.iteritems():
                if mote_key in region_motes:
                    filtered_motes[mote_key] = mote_item
            
            ax = fig.add_subplot(grid_size_x, grid_size_y, position)            
            ax.set_title(region_name)
            plot(ax, filtered_motes, highlight_filename, custom_func_mote, custom_func)            
            position += 1        
    else:
        ax = fig.add_subplot(111)        
        plot(ax, motes, highlight_filename, custom_func_mote, custom_func, color_code_filename)
    
    pyplot.tight_layout(rect=[0, 0, .97, 1], pad=3.0)
    if '-bench' not in args:                    
        pyplot.show()
    
    #fig.savefig('exp.png')

if __name__ == "__main__":    
    main(sys.argv)
