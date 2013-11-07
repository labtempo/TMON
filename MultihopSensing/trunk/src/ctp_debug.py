import math
from TOSSIM import *
from tinyos.tossim.TossimApp import *

# Includes the lib path
import os, sys
from SharedLibs.tools import *

MAX_ITERATIONS = 100000000
MAX_TIME = 15 * 60 #s
BOOT_T0 = 2351217 # should be > 0
BASE_NODE_ID = 255
MIDDLE_NODE_ID = 254
FREE_NODE_ID = 253

def main():
    print 'Starting...'
     
    vars = []    
    t = Tossim(vars)
    
    r = t.radio()
    
    t.addChannel("Boot", sys.stdout)
    t.addChannel("Temp", sys.stdout)
    t.addChannel("Radio", sys.stdout)
    t.addChannel("Error", sys.stderr)
    t.addChannel("TreeRouting", sys.stdout)
    t.addChannel("TreeRoutingCtl", sys.stdout)
    
    topology = cStringIO.StringIO("""
    255 254 -66
    254 255 -66
    253 254 -66
    254 253 -66    
    """)
    nodes = read_topology(topology, t)
    
    applyNoiseModel(nodes)
    
    # Random boot is recommended for sane behavior
    random_boot(nodes, BOOT_T0)
        
    #show_connections(nodes, r)
    
    advance_to_posboot(nodes, t)
    
    bridge_node_is_off = False
    
    loop_counter = 0    
    max_ticks = MAX_TIME * t.ticksPerSecond()
    BRIDGE_NODE_OFF = BOOT_T0 + 3 * 60 * t.ticksPerSecond() # 3 minutes after BOOT_TO
    
    curr_time = t.time()
    while loop_counter < MAX_ITERATIONS and curr_time < max_ticks:
        curr_time = t.time()
        print "T:", curr_time
        t.runNextEvent()           
        loop_counter += 1
        if not bridge_node_is_off and curr_time > BRIDGE_NODE_OFF:
            r.add(BASE_NODE_ID, FREE_NODE_ID, -66.)
            r.add(FREE_NODE_ID, BASE_NODE_ID, -66.)
                             
            r.remove(BASE_NODE_ID, MIDDLE_NODE_ID)
            r.remove(MIDDLE_NODE_ID, BASE_NODE_ID)            
            r.remove(FREE_NODE_ID, MIDDLE_NODE_ID)
            r.remove(MIDDLE_NODE_ID, FREE_NODE_ID)
            
            bridge_node = t.getNode(MIDDLE_NODE_ID)
            bridge_node.turnOff()
            bridge_node_is_off = True            
            print "CHANGED!" * 10
        
    
    print 'Done. Loops = %d, curr_time = %s / %s' % (loop_counter, curr_time / 10.**9, max_ticks / 10.**9)


if __name__ == "__main__":
    main()
