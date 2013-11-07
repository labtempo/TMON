import random
import sys
import os
import cStringIO
import math
import subprocess
import socket
from collections import OrderedDict

try:
    import gzip
except ImportError:
    gzip = None

MAX_INT = sys.maxint
GZIP_COMPRESSION_RATIO = 0.01 # used to estimate the file size when a gzipped file is unzipped

#Execution modes for execCmd()
LOCAL_EXEC = 0
SSH_EXEC = 1
REMOTE_DAEMON_EXEC = 2
KNOWN_EXEC_MODES = [LOCAL_EXEC, SSH_EXEC, REMOTE_DAEMON_EXEC]


def read_file(filename, max_file_size= 1024 ** 3):
    '''
    This function attempts to read the whole file into memory at once.
    If the file is too big, then it returns None.
    Warning: this function won't close the file and will mess with the file pointer.
    
    @param max_file_size: maximum size of file to attempt a full read in bytes.
    '''
    file_size = os.path.getsize(filename)
    is_gzipped = filename.endswith('.gz')
    
    if (is_gzipped and file_size < max_file_size * GZIP_COMPRESSION_RATIO) or \
       (not is_gzipped and file_size < max_file_size):
        f = open_file(filename)
        try:
            contents = f.read().splitlines()
        finally:
            if f:
                f.close()
        return contents    
    return None
        

def open_file(filename, mode="r"):
    '''
    Opens a text file or gzipped text file
    @returns: file or None
    '''
    if not filename:
        return None
    if filename.endswith(".gz"):
        if not gzip:
            return None
        if 'b' not in mode:
            mode += 'b'
        return gzip.open(filename, mode)
    else:
        # Assumes a regular text file
        return open(filename, mode)

def sendMsg(host, msg, port):
    '''
    Sends a UDP message to dvs_daemon
    '''
    sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sendSocket.connect((host, port))
        sendSocket.send(msg)
    finally:
        sendSocket.close()
        

def execCmd(cmd, dest=None, wait=True, shell=False, mode=LOCAL_EXEC):
    '''
    Executes a command, waits for it to finish and returns a string output.
    'cmd' is a list with the first element being the program, and the others its arguments.
    Set 'wait' to false if you don't want to wait for the process to finish. Note that the
    output produced by the process won't be returned if 'wait' is False.
    
    If a login is given, shell is forced False. 
    '''
    assert isinstance(cmd,list) #can't execute a None command
    assert mode in KNOWN_EXEC_MODES #needs to specify the correct mode
    
    if mode != LOCAL_EXEC:
        assert dest is not None #must know the destination
    
    if mode == SSH_EXEC:
        cmd[:0] = ['ssh', dest] #appends ssh to the command
        shell = False #forces shell to be false
       
    if wait:
        p = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=shell)
        return p.communicate()[0]
    else:
        subprocess.Popen(cmd,shell=shell)


'''
The CPM noise model needs at least 100 samples to work properly.
source: http://docs.tinyos.net/tinywiki/index.php/TOSSIM
'''
_MIN_NOISE_SAMPLES = 100

def raw_to_volts_micaz(ADC):
    '''
    Corrected using average difference
    '''
    # (Estimated via Gnuplot's curve fit: 1.22592 * 1024 / ADC - 0.0140757)
    try:
        return (1.330 * 1024) / ADC - (0.6 + 0.404)
    except ZeroDivisionError, e:
        print e
        return 0
    

def raw_to_volts_iris(ADC):
    '''
    Estimated via Gnuplot's curve fit
    '''
    try:
        return  (1.107509766 * 1024) / ADC - 0.0166975
    except ZeroDivisionError, e:
        print e
        return 0


def raw_to_kelvin(ADC):
    if ADC == 0:
        return None

    a = 0.001010024
    b = 0.000242127
    c = 0.000000146
    R1 = 10000
    ADC_FS = 1023.
    Rth = R1 * float(ADC_FS - ADC) / ADC
    
    if Rth < 0:
        return None
        
    ln_Rth = math.log(Rth)
    TK = 1. / (a + (b * ln_Rth) + (c * (ln_Rth * ln_Rth * ln_Rth)))
    return TK


def kelvin_to_celcius(tk):
    return tk - 273.15


def raw_to_celcius(ADC):
    tk = raw_to_kelvin(ADC)
    
    if tk == None:
        return 0
    
    return kelvin_to_celcius(tk)


def read_topology(topo, tossim):
    '''
    Create nodes and links based on a topology file
    '''
    if isinstance(topo, str):
        f = open(topo, "r")
    elif isinstance(topo, cStringIO.OutputType) or isinstance(topo, cStringIO.InputType):
        f = topo
    else:
        raise Exception("Unsupported input variable %s" % (type(topo)))
    node_ids = set()
    try:
        radio = tossim.radio()
        for line in f:
            s = line.split()
            if s and s[0][0] != "#":
                source = int(s[0])
                target = int(s[1])
                radio.add(source, target, float(s[2]))
                node_ids.add(source)
                node_ids.add(target)
    finally:
        if f:
            f.close()
            
    return [tossim.getNode(i) for i in node_ids]


def create_complete_topology(nodes, gains=None, default_gain=-66):
    '''
    Creates a topology where all nodes are interconnected
    @param gain is a dict e.g. {(1, 2): -66, (1, 3): -99}
    @param nodes are a list of ids
    '''
    topology = cStringIO.StringIO()
    for i in nodes:
        for j in nodes:
            if i != j:
                if not gains:
                    gain = default_gain
                else:
                    gain = gains.get((i, j), default_gain)
                topology.write("%d %d %f\n" % (i, j, gain))
    topology.reset()
    return topology    


def unique_randint_gen(start, end):
    '''
    A randint generator that returns only unique values (not sorted before) 
    '''
    selected_values = []
    value = 0
    
    while len(selected_values) < (end - start + 1):
        while True:
            value = random.randint(start, end)
            if value not in selected_values:
                selected_values.append(value)
                break        
        yield value


def random_boot(nodes, base, gen=unique_randint_gen(1, 1000)):
    '''
    Boot all nodes with a random time value from a given base time
    @param nodes list o Tossim nodes
    @param base base int time in Tossim ticks
    @param gen a generator function from which to draw time values
    '''
    for node in nodes:
        node.bootAtTime(base + gen.next())
        

def show_connections(nodes, radio):
    # Print network info
    print 'Network connections:'
    for source in nodes:
        for target in nodes:
            if source != target:
                print '\t%d connected to %d ? %s' % (source.id(), target.id(), radio.connected(source.id(), target.id()))


def advance_to_posboot(nodes, tossim):
    while any(not n.isOn() for n in nodes):
        tossim.runNextEvent()


def applyNoiseModel(nodes, noise_filename="/opt/tinyos-2.1.1/tos/lib/tossim/noise/meyer-heavy.txt", samples_to_read=MAX_INT):
    sample_counter = 0
    if samples_to_read < _MIN_NOISE_SAMPLES:
        raise Exception("Minimum sample_size must be %d." % _MIN_NOISE_SAMPLES)
        
    noise = open(noise_filename, "r")
    try:
        for line in noise:
            s = line.strip()
            if s:
                for n in nodes:
                    n.addNoiseTraceReading(int(s))
                sample_counter += 1
                if sample_counter >= samples_to_read:
                    break

        for n in nodes:
            n.createNoiseModel()
    finally:
        noise.close();
        
def prepareNodeDeluge(idMote, numberSerialPort):
    print "Installing GoldenImage..."
    os.chdir("/opt/tinyos-2.1.1/apps/tests/deluge/GoldenImage")
    cmd = "make iris install,%d mib520, /dev/ttyUSB%d" % (idMote, numberSerialPort)  
    execCmd(cmd.split(), wait=True, shell=True)
    print"Clearing memory node..."
    for slot in range (0,3):
        cmd = "tos-deluge serial@/dev/ttyUSB%d:57600 -s" % (numberSerialPort+1)
        execCmd(cmd.split(), wait=True, shell=True)
        cmd = "tos-deluge serial@/dev/ttyUSB%d:57600 -e %d" % (numberSerialPort+1,slot)    
        execCmd(cmd.split(), wait=True, shell=True)
    print "Inserting golden image in flash memory..."
    os.chdir("/opt/tinyos-2.1.1/apps/tests/deluge/GoldenImage") 
    cmd = "make iris"   
    execCmd(cmd.split(), wait=True, shell=True)
    cmd = "tos-deluge serial@/dev/ttyUSB%d:57600 -i 0 build/iris/tos_image.xml" % (numberSerialPort+1)
    execCmd(cmd.split(), wait=True, shell=True) 


def parse_line(line):
    '''
    Parse column-based files.
    
    @return: (timestamp, mote_id, counter, temperature)
    
    This function is capable of handling three file formats:
        <timestamp> <temperature>
        <timestamp> <id> <temperature>
        <timestamp> <id> <counter> <temperature>
    '''
    if not line:
        return None
        
    tokens = line.split()
    
    timestamp = float(tokens[0])
    if len(tokens) == 2:
        # <timestamp> <temperature>
        mote_id = 1
        counter = None
        temperature = float(tokens[1])
    elif len(tokens) == 3:
        # <timestamp> <id> <temperature>
        mote_id = int(tokens[1])
        counter = None
        temperature = float(tokens[2])
    elif len(tokens) == 4:
        # <timestamp> <id> <counter> <temperature>
        mote_id = int(tokens[1])
        counter = int(tokens[2])
        temperature = float(tokens[3])
    else:
        raise Exception("Unknown line format: %s" % (line))

    return (timestamp, mote_id, counter, temperature)


def parse_arff_file(line_iter):
    '''
    Yield data lines
    '''
    data = OrderedDict()
    attrs = []
    for line in line_iter:
        line = line.strip()
        if line.startswith("@data"):
            break
        elif line.startswith("@attribute"):
            attr_name = line.split(" ")[1].strip()
            data[attr_name] = -1
            attrs.append(attr_name)
    
    for line in line_iter:
        line = line.strip()
        if line and not line.startswith(r"%") or line.startswith("@"):
            tokens = line.split(",")
            for i in xrange(len(tokens)):
                data[attrs[i]] = float(tokens[i])
            yield data
    
