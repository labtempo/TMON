'''
Created on Jul 4, 2012

@author: giulio
'''
from pylab import *
import matplotlib.pyplot as plt
from SharedLibs.tools import parse_line, open_file
import time, sys

TEMP_DRAW_THRESHOLD = 0.5
MAX_TEMP = 60.
MIN_TEMP = 15.

def normalize_temp(temp, min_temp=10., max_temp=100.):
    return (temp - min_temp) / (max_temp - min_temp)


def main(args):
    ion()
    grid(True)
    figure(1)
    
    frame1 = plt.gca()
    
    frame1.axes.get_xaxis().set_visible(False)
    frame1.axes.get_yaxis().set_visible(False)
    
    motes = {}
    
    temp_matrix = [ [MIN_TEMP for i in range(7)] for j in range(9) ]
    temp_matrix[-1][-1] = MAX_TEMP
    
    
    positions = { \
    # back
    248: (1,1), 247: (2,1), 252: (3,1), 238: (1,5), 244: (2,5), 243: (3,5),
    # front
    249: (6,1), 253: (7,1), 245: (8,1), 241: (6,5), 237: (7,5), 239: (8,5),
    }
    
    
    for mote_id, pos in positions.items():
        plt.text(pos[1], pos[0], str(mote_id), fontsize=12, horizontalalignment='center', verticalalignment='center', color="black")
    
    plt.text(1, 0, "Back R1", fontsize=12, horizontalalignment='center', verticalalignment='bottom', color="white")
    plt.text(5, 0, "Back R2", fontsize=12, horizontalalignment='center', verticalalignment='bottom', color="white")
    plt.text(1, 5, "Front R1", fontsize=12, horizontalalignment='center', verticalalignment='bottom', color="white")
    plt.text(5, 5, "Front R2", fontsize=12, horizontalalignment='center', verticalalignment='bottom', color="white")
    
    
    f = open_file("/home/giulio/Dropbox/Projeto Sensores/experiments/temperatura/sala_servidores/temps_25_05_12_15h09m48s.txt.gz")
    
    loaded_color_bar = False
    
    try:
        for line in f:
            #A = rand(5,5)
            #imshow(A, interpolation='nearest')
            values = parse_line(line)
            timestamp = values[0]
            mote_id = values[1]
            temp = values[-1]
            
            mote = motes.get(mote_id, None)
                   
            if mote is None or abs(mote["temp"] - temp) > TEMP_DRAW_THRESHOLD:            
                if mote is None:
                    mote = {"temp": temp, "timestamp": timestamp}
                    motes[mote_id] = mote
                else:
                    mote["temp"] = temp
                    mote["timestamp"] = timestamp
                
                pos = positions.get(mote_id, None)
                if pos is not None:
                    temp_matrix[pos[0]][pos[1]] = temp                               
                    
                    print "Drawing", mote_id, time.ctime(timestamp), temp
                    imgplot = imshow(temp_matrix, interpolation='nearest')
                    imgplot.set_cmap('jet')                
                    
                    if not loaded_color_bar:
                        plt.colorbar()
                        loaded_color_bar = True
                    
                    draw()
                    #time.sleep(.1)
    finally:        
        if f:
            f.close()


if __name__ == "__main__":
    main(sys.argv)