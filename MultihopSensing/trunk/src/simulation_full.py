############# imports ####################################
from TOSSIM import *
from tinyos.tossim.TossimApp import *
import math
import random
import sys

############ parameters ##################################

#the DBG Channels we want to listen to.
#DBG_CHANNELS = ['Boot','Ctrl','Radio','Temp','Battery','Light'] 
#               'Forwarder','FHangBug', 'CtpForwarder',
#                'Route', 'TreeRoutingCtl','TreeRouting',
#                'RoutingTimer','LITest']
DBG_CHANNELS = ['PacketForwarder']


#Set to True if you wan to log the dbg statements
LOG_DATAS = False


#The filename of the log file (if used)
LOG_FILENAME = "sim_log.txt"


#The maximum simulation time (after all the nodes have booted)
MAX_TIME =  30 * 10000000000 #equal 30 seconds


#Size of the area on X axis (in meters)
AREA_SIZE_X = 200


#Size of the area on Y axis (in meters)
AREA_SIZE_Y = 200


#Number of static nodes
STATIC_N = 100


#X size of the static grid
GRID_SIZE_X = 10


#Y size of the static grid
GRID_SIZE_Y = 10



#radio transmission params 
#theses params have been taken from inputFile.java from :
#http://www.tinyos.net/tinyos-2.x/doc/html/tutorial/usc-topologies.html
#from USC-ANRG.
#the rssi model used is the log-normal shadowing model use

D0 = 10             #reference distance (in meters)
PLD0 = 30.1  #52.1    #power decay for the reference distance D0 (in dB)
PLE = 3.3        #path loss exponent: rate at which signal decays
SSD = 3.0        #standard deviation of the noise (randomness due to multipath effect)

NOISE_TRACE_FILE = "meyer-heavy.txt"     #the file used to add some real noise to the simulation of the radio.
NOISE_SAMPLES = 300             #the maximal number of noise samples used for this process (if the file has less samples then less samples will be used)


####### FUNCTIONS ########################################

#this function return a gain value for a certain distance
def gain_from_dist(dist):
    GAIN = - PLD0 - 10 * PLE * math.log10(dist/D0) + random.gauss(0,SSD)
    return GAIN


#this function return the distance between nodes a and b
#if the parameter a is givent as [X,Y]
def dist(a,b):
    return math.sqrt(math.pow(a[0]-b[0],2) + math.pow(a[1]-b[1],2))


####### MAIN CODE ########################################


#if we log the datas we open a file.
if LOG_DATAS == True:
    f = open(LOG_FILENAME, "w")

#we start tossim core
n = NescApp()
t = Tossim(n.variables.variables())

#for all the DBG channels we want to listen to.
for i in DBG_CHANNELS:
    t.addChannel(i, sys.stdout)
    print 'Listening to channel ',i
    if LOG_DATAS == True:
        t.addChannel(i, f)


#we get the radio from Tossim.
r = t.radio()


print 'Creating static nodes positions'

#first we set the positions of the static nodes.
if STATIC_N != GRID_SIZE_X * GRID_SIZE_Y :
    raise AttributeError,'Error : The number of static nodes must be equal to grid size x * grid size y'

#the distance between nodes in the static grid.    
stepx = AREA_SIZE_X / (GRID_SIZE_X+1)
stepy = AREA_SIZE_Y / (GRID_SIZE_Y+1)

#this puts all the static nodes positions in static_nodes_pos
static_nodes_pos = [(i*stepx,j*stepy) for i in range (1,GRID_SIZE_X+1) for j in range (1,GRID_SIZE_Y+1)]

print 'Creating radio links'

#now we set the links for the static nodes.
for n in range(0,STATIC_N):
    for i in range(0,GRID_SIZE_X):
        for j in range(0,GRID_SIZE_Y):
            ntmp = (i*GRID_SIZE_X+j)
            if (n != ntmp):
                dtmp=dist(static_nodes_pos[n],static_nodes_pos[ntmp])
                gtmp=gain_from_dist(dtmp)
                print 'add link from ',n,' to ',ntmp,' with dist ',dtmp,' with gain ',gtmp
                r.add(n+1,ntmp+1,gtmp)
                r.add(ntmp+1,n+1,gtmp)



print 'Creating noise traces for links'        

#adding noise trace for sensors:
noise = open(NOISE_TRACE_FILE, "r")
lines = noise.readlines()
cnt = 0
for line in lines:
    if (cnt > NOISE_SAMPLES):
          break
    else:
        cnt=cnt+1
        str = line.strip()
        if (str != ""):
            val = int(str)
            for i in range(0,STATIC_N):
                t.getNode(i).addNoiseTraceReading(val)

for i in range(0,STATIC_N):
  print "Creating noise model for ",i;
  t.getNode(i).createNoiseModel()


print 'Setting ON all the nodes'    

#then we set ON all the static nodes
for i in range(0,STATIC_N):
    t.getNode(i).bootAtTime(10000+1000*i)


print 'Waiting for all the nodes to be ON'    

#then we run the simulation until all nodes are booted
while(not t.getNode(STATIC_N).isOn()):
    t.runNextEvent()

#we save the time before
stime = t.time()

print 'Starting simulation'
print 'Time before main loop',stime

#until MAX time.
while(MAX_TIME  > t.time()-stime):
    node = t.getNode(i)
    t.runNextEvent()
#    print node.getVariable("MultihopOscilloscopeC.packetsToNetwork").getData()
#    print node.getVariable("MultihopOscilloscopeC.packetsToSerial").getData()

    
# Counter of packets 
#packetsToSerial = 0
#packetsToNetwork = 0
#for i in range(0,STATIC_N):
#    node = t.getNode(i)
#    packetsToSerial = packetsToSerial + (int)(node.getVariable("MultihopOscilloscopeC.packetsToSerial").getData())
#    packetsToNetwork = packetsToNetwork + (int)(node.getVariable("MultihopOscilloscopeC.packetsToNetwork").getData())
#   
#print 'Number of packets forwarded = ',packetsToNetwork
#print 'Number of packets received = ',packetsToSerial
#print 'Efficiency of network = ',packetsToSerial/packetsToNetwork*100




    



    
    