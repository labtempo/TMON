'''
Created on Aug 11, 2012

@author: Giulio

A class that will parse traces from various formats.
'''

from SharedLibs.tools import open_file, GZIP_COMPRESSION_RATIO
from collections import OrderedDict
import os


class TraceParserException(Exception):
    pass


def extract_file_type(filename):
    tokens = filename.split(".")
    file_type = None
    for t in reversed(tokens[1:]):
        if t != "gz":
            file_type = t
            break
    return file_type


class AutoInterpolationWrapper(object):
    MAX_DIFF = 1.5
    
    def __init__(self, parse_func):
        self.parse_func = parse_func
        self.last_result = None
    
    def __call__(self, line):
        result = self.parse_func(line)
        if result is not None:
            if self.last_result:
                while True:
                    ts_diff = result['timestamp'] - self.last_result['timestamp']
                    if ts_diff > self.MAX_DIFF:
                        self.last_result['timestamp'] += 1
                        return self.last_result
                    else:
                        break
            self.last_result = result
            return result


class AutoTimestampsWrapper(object):
    def __init__(self, parse_func):
        self.parse_func = parse_func
        self.auto_ts = 1
    
    def __call__(self, line):
        if line:
            line = ("%d," % self.auto_ts) + line
            self.auto_ts += 1
            result = self.parse_func(line)
            return result


class SuppressRapidChangesWrapper(object):
    def __init__(self, parse_func):
        self.parse_func = parse_func
        self.threshold = 1
        self.last_readings = None
    
    def __call__(self, line):
        if line:
            parse_result = self.parse_func(line)
            result = parse_result
            if result:
                if isinstance(parse_result, dict):       
                    if self.last_readings and (parse_result['timestamp'] - self.last_readings['timestamp'] < self.threshold):                        
                        result = None
                    self.last_readings = parse_result
                else: # assume col format
                    if not self.last_readings:
                        self.last_readings = {}
                    else:                        
                        if parse_result[0] - self.last_readings.get(parse_result[1], 0) < self.threshold:                            
                            result = None                            
                    self.last_readings[parse_result[1]] = parse_result[0]
            return result


class TraceReader(object):
    '''
    Reads and parse traces from files.
    '''

    def __init__(self, filename, supress_repetitions=False, auto_timestamps=True, auto_interpolation=False, \
                 suppress_rapid_changes=False, motes_to_ignore=None):
        '''
        @param supress_repetitions: when active, will suppress outputing repetitions 
        that may occur on traces.
        '''
        self.fp = None
        self.filename = filename
        self.file_type = extract_file_type(filename)
        self.read = self.parse # alias
        self.auto_timestamps = auto_timestamps # indicates that automatic timestamps are wanted
        self.use_auto_timestamps = False # set to True when it is detected that the file has no timestamps       
        self.arff_attributes = None
        self.suppress_rapid_changes = suppress_rapid_changes
        self.auto_interpolation = auto_interpolation        
        self.motes_to_ignore = motes_to_ignore if motes_to_ignore else []
        
        if not self.file_type == "arff" and self.auto_interpolation:
            raise TraceParserException("Interpolation is only currently supported on arff files.")
        
        self.reset()
    
    def reset(self):
        self.close()
        self.fp = open_file(self.filename)
        if self.file_type == "arff":
            self.arff_attributes = self._parse_arff_header()
            
    def close(self):
        '''
        We need to make sure the file is closed.
        The attribute check is recommended since __init__ may fail and __del__ will
        be called anyway.
        '''
        if hasattr(self, "fp"):
            if self.fp:
                self.fp.close()
    
    
    def __del__(self):        
        self.close()
        
    def __iter__(self):
        return self.parse()
    
    
    def _parse_arff_header(self):
        attributes = []
        if not self.fp:
            self.fp = open_file(self.filename)        
                
        for line in iter(self.fp):                
            if line.startswith("@data"):
                break
            elif line.startswith("@attribute"):
                attr_name = line.split()[1]      
                attributes.append(attr_name)
        
        if "timestamp" not in attributes and self.auto_timestamps:
            attributes.insert(0, "timestamp")
            self.use_auto_timestamps = True
        return attributes
    
    
    def _parse_colfile(self, line):
        '''
        Parse column-based files.
        
        @return: (timestamp, mote_id, counter, temperature)
        
        This function is capable of handling three file formats:
            <timestamp> <temperature>
            <timestamp> <id> <temperature>
            <timestamp> <id> <counter> <temperature>
        '''
        if not line or line.startswith("#"):
            return None
            
        tokens = map(float, line.split())
        
        timestamp = tokens[0]
        if len(tokens) == 2:
            # <timestamp> <temperature>
            mote_id = 1
            counter = None
            temperature = tokens[1]
        elif len(tokens) == 3:
            # <timestamp> <id> <temperature>
            mote_id = int(tokens[1])
            counter = None
            temperature = tokens[2]
        elif len(tokens) == 4:
            # <timestamp> <id> <counter> <temperature>
            mote_id = int(tokens[1])
            counter = int(tokens[2])
            temperature = tokens[3]
        else:
            raise Exception("Unknown line format: %s" % (line))
        
        if mote_id not in self.motes_to_ignore:        
            return (timestamp, mote_id, counter, temperature)
    
    
    def _parse_arfffile(self, line):
        if line and not line.startswith(r"%"):
            data = OrderedDict()
            tokens = map(float, line.split(","))
            for i in xrange(len(tokens)):
                data[self.arff_attributes[i]] = tokens[i]
            for mote in self.motes_to_ignore:
                if mote in data.iterkeys():                    
                    del data[mote]            
            return data
        return None
    
    
    def _parse_aggfile(self, line):
        '''
        timestamp         id count temp      light volt
        1349364567.075451 30 0     -2.751112 237   2.952124
        '''
        if not line:
            return None
        
        tokens = line.split()
        if len(tokens) != 6:
            return None
        
        timestamp = float(tokens[0])
        mote_id = int(tokens[1])
        counter = float(tokens[2])
        temp = float(tokens[3])
        light = int(tokens[4])
        volt = float(tokens[5])
        
        return (timestamp, mote_id, counter, temp, light, volt)
        
    
    def parse(self):
        '''
        Implements a generator interface for many types of files
        '''
        try:
            parse_func = None
            if self.file_type == "txt":
                parse_func = self._parse_colfile                
            elif self.file_type == "arff":         
                parse_func = self._parse_arfffile
            elif self.file_type == "agg":
                parse_func = self._parse_aggfile
            else:
                raise TraceParserException("File type '%s' is unknown" % self.file_type)
            
            if self.suppress_rapid_changes:
                parse_func = SuppressRapidChangesWrapper(parse_func)
            
            if self.use_auto_timestamps:
                parse_func = AutoTimestampsWrapper(parse_func)
            
            if self.auto_interpolation:
                parse_func = AutoInterpolationWrapper(parse_func)
                        
            for line in self.fp:
                result = parse_func(line)
                if result is not None:                                          
                    yield result
        finally:
            if self.fp:
                self.fp.close()


class TraceWriterException(Exception):
    pass


class TraceWriter(object):
    def __init__(self, filename, arff_attributes=None):
        self.output_type = extract_file_type(filename)
        if self.output_type == "arff" and arff_attributes is None:
            raise TraceWriterException("Must specify the arff file attributes")
        if self.output_type != "arff" and arff_attributes is not None:
            raise TraceWriterException("Error, specified arff attributes for a non arff output. Detected output was' %s'" % \
                                       self.output_type)
        
        if self.output_type not in ["arff", "txt"]:            
            raise TraceWriterException("Uknown format '%s'" % self.output_type)
            
        self.output = open(filename, "w")         
        self.arff_attributes = arff_attributes
        if self.output_type == "arff":
            self._write_header(arff_attributes)
                        
        
    def _write_header(self, arff_attributes):
        self.output.write("@relation database\n\n")
        for attr in arff_attributes:
            self.output.write("@attribute %s numeric\n" % attr)        
        self.output.write("\n@data\n")
    
    def write(self, data):
        if self.output_type == "arff":            
            self.output.write(",".join(str(value) for value in data.values()))            
        elif self.output_type == "txt":                        
            self.output.write(" ".join(str(value) for value in data))
        self.output.write("\n")
        
    def close(self):
        if self.output:
            self.output.close()
            

class Raw2ArffWrapper(object):
    def __init__(self, tracereader):
        self.tracereader = tracereader
        self.parse_gen = self.tracereader.parse()      
        self.mote_ids, self.data_buffer = self._fast_preprocessing(self.parse_gen)
    
    def _fast_preprocessing(self, parse_gen):
        '''
        Reads a chunk of data, proportional to the size of the file. This is assumed to be enough
        for preprocessing.
        '''
        filesize = os.path.getsize(self.tracereader.filename)
        if ".gz" in self.tracereader.filename:
            filesize *= 1. / GZIP_COMPRESSION_RATIO
        
        data_buffer = [] # this will be given back to the parse function afterwards
        
        if filesize > 1024 ** 2:
            '''
            When the file is "big" we just read a chunk of it.
            The chunk is determined by a crude approximation of lines to read.
            '''
            max_line_size = 10 * 200 # characters (bytes)
            approx_line_count = filesize / max_line_size
            lines_to_read = int(0.30 * approx_line_count)
                        
            for _ in xrange(lines_to_read):
                data_buffer.append(parse_gen.next())
        else:
            for data in parse_gen:
                data_buffer.append(data)
        
        # analyze the data for the mote's ids
        mote_ids = set()
        for data in data_buffer:
            mote_ids.add(data[1])
        
        mote_ids = list(mote_ids)        
        mote_ids.sort()
                
        return mote_ids, data_buffer
    
    
    def parse(self):
        # initialize stacks                                
        stacks = {}
        for m in self.mote_ids:
            stacks[m] = []                    
        
        current_time = None             
        while True:                    
            if self.data_buffer:
                values = self.data_buffer.pop(0)
            else:
                try:
                    values = self.parse_gen.next()
                except StopIteration:
                    break     
                               
            timestamp = values[0]
            mote_id = values[1]                
            data = values[-1]
            self._update_stacks(mote_id, stacks, (timestamp, data))
            if all(stacks.values()):                        
                if not current_time:
                    current_time = float(sum(s[0][0] for s in stacks.values())) / len(stacks)
                                       
                while timestamp >= current_time:
                    t = self._join_stacks(stacks, current_time)                    
                    d = OrderedDict()
                    d["timestamp"] = t[0]
                    for i in xrange(len(self.mote_ids)):
                        d["mote_%d" % self.mote_ids[i]] = t[i + 1]
                    current_time += 1
                    yield d
                            

    def _update_stacks(self, mote_id, stacks, data, time_delta=1.5):
        if not mote_id in stacks:
            raise TraceParserException("Mote id not recognized: %d" % mote_id)    
        stacks[mote_id].append(data)
        

    def _join_stacks(self, stacks, current_time):
        # remove old data  
        for s in stacks.values():
            while len(s) > 1 and s[1][0] <= current_time:
                del s[0]
        # make the output uniform
        if all(stacks.values()):
            result = [current_time]            
            result += [s[0][1] for s in stacks.values()]        
            return result
        
        return []


class Agg2RawWrapper(object):
    def __init__(self, tracereader, attribute_selector):
        self.tracereader = tracereader
        self.parse_gen = self.tracereader.parse()
        self.attribute_selector =  attribute_selector        
    
    def parse(self):
        for data in self.parse_gen:
            result = list(data[:3]) 
            result.append(data[self.attribute_selector])
            yield tuple(result)
    

RAW_FILE_FORMAT = 0
UNIFORM_FILE_FORMAT = 1
RAW_AGGREGATE_FILE_FORMAT = 2
FILE_FORMATS = (RAW_FILE_FORMAT, UNIFORM_FILE_FORMAT, RAW_AGGREGATE_FILE_FORMAT)

TEMP = 3
LIGHT = 4
VOLT = 5


class TraceAdapter(object):
    '''
    Adapts a trace input to other outputs. 
    
    The main usage is very straightforward:
    1. Create a TraceReader object (e.g. tracereader)
    2. Pass the tracereader on the TraceAdapter creation (e.g. traceadapter = TraceAdapter(tracereader, UNIFORM_FILE_FORMAT)
    3. By calling parse, you get the processed output on the desired file format.
    
    @todo: implement uniform to raw conversion    
    '''
    def __init__(self, tracereader, out_format, *wrapper_params):
        assert out_format in FILE_FORMATS
        
        self.tracereader = tracereader
        self.out_format = out_format
        self.arff_attributes = None
        self.parse_gen = None
        
        # initialization
        if self.out_format == UNIFORM_FILE_FORMAT:
            self.parser = Raw2ArffWrapper(self.tracereader)            
            self.arff_attributes = ["timestamp"] + ["mote_%d" % mote_id for mote_id in self.parser.mote_ids]
        elif self.out_format == RAW_FILE_FORMAT:
            self.parser = Agg2RawWrapper(self.tracereader, *wrapper_params)
        
        self.parse_gen = self.parser.parse()
    
    def parse(self):
        '''
        Assumes that ARFF input implies UNIFORM_FILE_FORMAT
        Assumes that TXT input implies RAW_FILE_FORMAT
        '''
        if not self.parse_gen:
            self.parse_gen = self.tracereader.parse()
                                        
        for data in self.parse_gen:
            yield data