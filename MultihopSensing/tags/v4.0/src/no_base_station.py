import math
from TOSSIM import *
from tinyos.tossim.TossimApp import *

# Includes the lib path
import os, sys
sys.path.append(os.environ['HOME'] + '/Dropbox/Projeto Sensores/apps/lib')
from tools import *

MAX_ITERATIONS = 100000000
MAX_TIME = 12 * 60 * 60 #s
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
    t.addChannel("Error", sys.stderr)
    
    topology = 'no_base_station_top.txt'
    #topology = create_complete_topology(range(NODE_COUNT))
    nodes = read_topology(topology, t)
    
    applyNoiseModel(nodes)
    
    # Random boot is recommended for sane behavior
    random_boot(nodes, BOOT_T0)
        
    #show_connections(nodes, r)
    
    advance_to_posboot(nodes, t)
        
    max_ticks = MAX_TIME * t.ticksPerSecond()
    loop_counter = 0
    while t.runNextEvent() and t.time() < max_ticks:        
        loop_counter += 1
       
    
    print 'Done.'


if __name__ == "__main__":
    main()
