'''
Created on Jun 20, 2012

@author: giulio
'''
import sys

from SharedLibs.tools import parse_line, open_file

'''
Main Classes
'''
VOLTAGE_READING = 0
TEMP_READING = 1

NAIVE_MODE = 0
ADDITIVE_MODE = 1
DEADZONE_MODE = 2


class GenericException(Exception):
    pass

class SensorNode(object):
    def __init__(self, node_id, basestation):
        self.node_id = node_id
        self.basestation = basestation # list of nodes
        self.neighbors = set()
        self.sent_count = 0
        self.received_count = 0
        self.snooped_count = 0
        self.send_start = 0
        self.send_end = 0        
    
    def snoop_reading(self, reading):
        # overhears traffic
        self.snooped_count += 1        
        
    def broadcast_reading(self, reading):
        # annouce the reading to all neighbors and the base node
        for neighbor in self.neighbors:
            neighbor.snoop_reading(reading)
        self.basestation.receive(reading)
        self.sent_count += 1
        if self.send_start == 0:
            self.send_start = reading.timestamp
        self.send_end = reading.timestamp

    def feed_reading(self, reading):
        ''' 
        Feed a file reading to the mote.
        The default behavior is to broadcast it.
        '''
        self.broadcast_reading(reading)        

    def get_stats(self):
        msg_period = (self.send_end - self.send_start) / self.sent_count 
        
        return "Sent: %5d (1 message every %f seconds)  Received: %d  Snooped: %d  Total Listened: %d" % \
            (self.sent_count, msg_period, self.received_count, self.snooped_count, \
             self.received_count + self.snooped_count)
    
    def __repr__(self):
        return "<Node %d>" % self.node_id


class Message(object):
    pass


class ReadingMessage(Message):
    def __init__(self, timestamp, node_id, value, counter, reading_type=TEMP_READING):
        self.timestamp = timestamp
        self.node_id = node_id
        self.value = value
        self.counter = counter        
        self.reading_type = reading_type        
    
    def to_line(self):
        # <timestamp> <id> <counter> <temperature>
        if self.counter is None:            
            return "%f %d %f\n" % (self.timestamp, self.node_id, self.value)
        return "%f %d %d %f\n" % (self.timestamp, self.node_id, self.counter, self.value)
    
    def __repr__(self):
        return "t=%s, node=%s, value=%s, counter=%s, type=%s" % (self.timestamp, self.node_id, self.value, \
                                                                 self.counter, self.reading_type)
            

class BaseStation(object):
    def __init__(self, output_file):
        self.output_file = output_file
    
    def receive(self, msg):
        # receive and process messages from other nodes
        if isinstance(msg, ReadingMessage):
            self.save_reading(msg)
        else:
            raise Exception("Uknown message type: %s" % type(msg).__name__)
    
    def save_reading(self, reading):
        # save a temperature or voltage measurement
        self.output_file.write(reading.to_line())

'''
Additive increase
'''
class AdditiveSensorNode(SensorNode):
    def __init__(self, node_id, basestation, min_interval, max_interval, increment):
        SensorNode.__init__(self, node_id, basestation)
        self.last_temp = None
        self.min_interval = int(min_interval)
        self.max_interval = int(max_interval)
        self.curr_interval = self.min_interval
        self.increment = int(increment)
        
        
    def feed_reading(self, reading):
        if reading.reading_type == TEMP_READING:
            if self.last_temp is None:        
                self.last_temp = reading
                self.broadcast_reading(reading)
            else:
                delta_time = reading.timestamp - self.last_temp.timestamp
            
                if delta_time >= self.curr_interval: # time to sample it
                    if reading.value != self.last_temp.value: # if it is different, send it and decrease the interval                
                        self.curr_interval = max(self.curr_interval - self.increment, self.min_interval)
                        self.broadcast_reading(reading)                        
                    elif delta_time >= self.max_interval: # send it anyway
                        self.broadcast_reading(reading)
                    else:
                        self.curr_interval = min(self.curr_interval + self.increment, self.max_interval)
                        
                    self.last_temp = reading
        else: 
            # broadcast everything else
            self.broadcast_reading(reading)


'''
Deadzone Sensor
'''
class DeadzoneSensorNode(SensorNode):
    def __init__(self, node_id, basestation, delta, max_period):
        SensorNode.__init__(self, node_id, basestation)
        self.last_temp = None
        self.delta = float(delta)
        self.max_period = float(max_period)
        
    def feed_reading(self, reading):
        if reading.reading_type == TEMP_READING:
            if self.last_temp is None:        
                self.last_temp = reading
                self.broadcast_reading(reading)
            else:
                delta_temp = abs(self.last_temp.value - reading.value)

                if delta_temp >= self.delta or (reading.timestamp - self.last_temp.timestamp > self.max_period):
                    self.broadcast_reading(reading)
                    self.last_temp = reading
        else: 
            # broadcast everything else
            self.broadcast_reading(reading)

            
'''
Utility Functions
'''           
def get_node(node_id, nodes, basestation, mode=NAIVE_MODE, mode_args=None):
    node = nodes.get(node_id, None)
    if not node:
        if mode == NAIVE_MODE:
            node = SensorNode(node_id, basestation)
        elif mode == ADDITIVE_MODE:
            node = AdditiveSensorNode(node_id, basestation, *mode_args)
        elif mode == DEADZONE_MODE:
            node = DeadzoneSensorNode(node_id, basestation, *mode_args)
        else:
            raise Exception("Unexpected mode %d" % mode)
        nodes[node_id] = node  
    return node
    

def read_topology(filename, basestation, mode=NAIVE_MODE, mode_args=None):
    f = open(filename)
    nodes = {}
    try:
        for line in f:
            line = line.strip()
            if line:
                neighborhood = []
                node_ids = map(int, line.split())
                for node_id in node_ids[1:]:
                    node = get_node(node_id, nodes, basestation, mode, mode_args)
                    neighborhood.append(node)
                # central node
                nexus = get_node(node_ids[0], nodes, basestation, mode, mode_args)
                nexus.neighbors = neighborhood            
    finally:
        if f:
            f.close()
    
    return nodes


def get_option_parameters(args, option, arg_count=1):
    if option in args:
        index = args.index(option)
        if arg_count == 1:
            if index + 1 < len(args):
                return args[index + 1]
            else:
                return None
        if index + arg_count <= len(args):            
            return args[index + 1: index + arg_count]
    return None


def auto_update_topology(node_id, nodes, basestation, mode=NAIVE_MODE, mode_args=None):
    # create automatically the topology
    temp_node = get_node(node_id, nodes, basestation, mode, mode_args)
    
    # update all neighbors
    for node in nodes.values():
        if node != temp_node:
            temp_node.neighbors.add(node)
            node.neighbors.add(temp_node)
    
    nodes[node_id] = temp_node
    
    return temp_node
    

def main(args):
    if len(args) < 2 or '-h' in args:
        print "Usage: python %s {temp_file} [-t topology_file] [-b battery_file] [-at artificial timestamps] [-m naive (default) | additive {min, max, incr} | deadzone {delta, max_period}]" % (args[0])
        exit()
    
    if '-at' in args and '-b' in args:
        print 'Impossible to use -at mode with -b'
        exit()
        
    artificial_timestamps = '-at' in args
    
    f_temps = open_file(args[1])
    batt_filename = get_option_parameters(args, '-b')
    
    mode = NAIVE_MODE
    mode_args = None
    if '-m' in args:
        mode_str = get_option_parameters(args, '-m')
        if mode_str == 'additive': 
            mode = ADDITIVE_MODE
            mode_args = get_option_parameters(args, '-m', 5)
            if mode_args is None:
                raise GenericException("Missing additive parameters")
            del mode_args[0]
        elif mode_str == 'deadzone':
            mode = DEADZONE_MODE
            mode_args = get_option_parameters(args, '-m', 4)
            if mode_args is None:
                raise GenericException("Missing deadzone parameters")
            del mode_args[0]
        elif mode_str is None:
            raise GenericException("Could not parse arguments of -m")
        else:
            raise GenericException("Unexpected mode %s" % mode_str)
    
    output = open("output.txt", "w")    
    if batt_filename:
        f_batt = open_file(batt_filename)
    else:
        f_batt = None
        
    try:
        basestation = BaseStation(output)
        
        topology_filename = get_option_parameters(args, '-t')
        if topology_filename:
            nodes = read_topology(topology_filename, basestation, mode, mode_args)            
        else:
            '''
            If a topology is not specified, the network will include the nodes as they
            appear in the file.
            '''
            nodes = {}
        
        batt_info = None
        if f_batt:
            batt_line = f_batt.readline()
            if batt_line:
                batt_info = parse_line(batt_line)
        
        artificial_ts = {}
        
        for temp_line in f_temps:
            timestamp, node_id, counter, temperature = parse_line(temp_line)
            
            if artificial_timestamps:                
                timestamp = artificial_ts.get(node_id, 0)
                if timestamp == 0:
                    artificial_ts[node_id] = 1
                else:
                    artificial_ts[node_id] += 1
            
            temp_reading = ReadingMessage(timestamp, node_id, temperature, counter, TEMP_READING)            
            temp_node = nodes.get(node_id, None)
            
            if temp_node is None:
                if not topology_filename:
                    temp_node = auto_update_topology(node_id, nodes, basestation, mode, mode_args)
                else:
                    raise GenericException("Node %d is outside topology!" % node_id)
            
            # handle battery
            while batt_info and batt_info[0] < timestamp: # send another batt_info now                
                batt_reading = ReadingMessage(batt_info[1], batt_info[0], batt_info[3], batt_info[2], VOLTAGE_READING)
                batt_node = nodes[batt_info[1]]
                batt_node.feed_reading(batt_reading)
                
                # update
                batt_line = f_batt.readline()
                if batt_line:
                    batt_info = parse_line(batt_line)
            
            temp_node.feed_reading(temp_reading)
    finally:
        if f_temps:
            f_temps.close()
        if f_batt:
            f_batt.close()
        if output:
            output.close()
    
    for node in nodes.values():
        print "Node %03d :" % (node.node_id), node.get_stats()
        
    print "All nodes: Sent: %d (1 message every %f seconds) Received: %d" % \
    (sum( (n.sent_count for n in nodes.values()) ), \
     sum( ((float(n.send_end - n.send_start) / n.sent_count) / len(nodes.values()) for n in nodes.values()) ), \
     sum( (n.received_count for n in nodes.values()) ) + \
     sum( (n.snooped_count for n in nodes.values()) ) ) 
   
if __name__ == '__main__':
    main(sys.argv)