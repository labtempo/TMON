import math
from TOSSIM import *
from tinyos.tossim.TossimApp import *

# Includes the lib path
import os, sys
sys.path.append(os.environ['HOME'] + '/Dropbox/Projeto Sensores/apps/lib')
from tools import *

MAX_ITERATIONS = 100000000
MAX_TIME = 60 * 60 #s
BOOT_T0 = 2351217 # should be > 0
NODE_COUNT = 10

def main():
    print 'Starting...'
    
    n = NescApp()    
    vars = n.variables.variables() 
    #vars = []    
    t = Tossim(vars)
    
    r = t.radio()
    
    #t.addChannel("Boot", sys.stdout)
    #t.addChannel("Temp", sys.stdout)
    #t.addChannel("Radio", sys.stdout)
    #t.addChannel("Error", sys.stderr)
    
    #topology = 'topology.txt'
    topology = create_complete_topology(range(NODE_COUNT))
    nodes = read_topology(topology, t)
    
    applyNoiseModel(nodes)
    
    # Random boot is recommended for sane behavior
    random_boot(nodes, BOOT_T0)
        
    #show_connections(nodes, r)
    
    advance_to_posboot(nodes, t)
    
    loop_counter = 0
    last_round_msgs = 0
    root = t.getNode(0)
    lost = 0
    received_from_all = 2**(NODE_COUNT + 1) - 1
    round_count = 0
    max_ticks = MAX_TIME * t.ticksPerSecond()
    while t.runNextEvent() and loop_counter < MAX_ITERATIONS and t.time() < max_ticks:
        round_msgs = root.getVariable("MultihopOscilloscopeC.round_msgs").getData()
                
        if round_msgs != last_round_msgs:            
            if last_round_msgs > round_msgs and round_msgs != received_from_all:
                lost += 1
            round_count += 1
            #print "Root status: %s" % bin(round_msgs)
            
        last_round_msgs = round_msgs
        loop_counter += 1
    
    print 'Lost %d messages out of %d (%f%%)' %(lost, round_count, float(lost * 100)/round_count)    
    
    print 'Done.'


if __name__ == "__main__":
    main()
