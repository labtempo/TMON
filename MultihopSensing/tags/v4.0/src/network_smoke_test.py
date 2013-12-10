import math
from TOSSIM import *
from tinyos.tossim.TossimApp import *

# Includes the lib path
import os, sys
from SharedLibs.tools import *

MAX_ITERATIONS = 100000000
MAX_TIME = 5 * 60 #s
BOOT_T0 = 2351217 # should be > 0
NODE_COUNT = 5

def main():
    print 'Starting...'
     
    vars = []    
    t = Tossim(vars)
    
    r = t.radio()
    
    t.addChannel("Boot", sys.stdout)
    t.addChannel("Temp", sys.stdout)
    t.addChannel("Radio", sys.stdout)
    t.addChannel("Error", sys.stderr)
    
    #topology = create_complete_topology(range(NODE_COUNT))
    topology = cStringIO.StringIO("""
    255 10 -66
    10 255 -66
    20 10 -66
    10 20 -66
    254 20 -66
    20 254 -66
    253 20 -66
    20 253 -66
    252 253 -66
    253 252 -66
    """)
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
        loop_counter += 1
    
    print 'Done.'


if __name__ == "__main__":
    main()
