'''
Created on Aug 18, 2012

@author: Giulio


'''
import sys
import numpy
from SharedLibs.tools import open_file

try:
    import matplotlib
    matplotlib.use('QT4Agg')
    import pylab
except ImportError:
    print "You must install pylab if you intend to plot stuff"
    exit()
    

def main(args):
    if len(args) < 2:
        print "Usage: python %s {hidden_vars_file} [-b (blame_file)]" % (args[0])
        exit()
    
    hidden_vars = [[]]    
            
    hv_file = open_file(args[1])
    try:
        for line in hv_file:
            line = line.strip()
            if line:
                values = map(float, line.split())
                for i in xrange(len(values) - len(hidden_vars) - 1):
                    hidden_vars.append([])
                for i in xrange(len(hidden_vars)):
                    if i > len(values) - 2:
                        hidden_vars[i].append((values[0], numpy.nan))
                    else:
                        hidden_vars[i].append((values[0], values[i + 1]))
    finally:
        hv_file.close()
    
    blame_file = open_file(args[args.index('-b') + 1]) if '-b' in args else None
    weights = []
    if blame_file:
        try:
            for line in blame_file:
                line = line.strip()
                if line:
                    values = map(float, line.split())
                    if not weights:
                        for i in xrange(len(values) - 1): # skip timestamp
                            weights.append([])
                    
                    for i in xrange(len(weights)):
                        weights[i].append([values[0], values[i + 1]])
        finally:
            blame_file.close()
        
        for w in weights:
            last = w[0][1]
            w[0][1] = 0
            for i in xrange(1, len(w)):
                aux = w[i][1]
                w[i][1] = (w[i][1] - last) ** 2
                last = aux
        
        
        size = 21
        for w in weights:
            for i in xrange(0, len(w) - size, size):
                avg = sum(w[i + j][1] for j in xrange(size)) / size
                for j in xrange(size):
                    w[i + j][1] = avg
        
        # filter poor motes
        cutoff = 5 * 1e-7
        avgs = []
        for w in weights:
            avg = sum(w[i][1] for i in xrange(len(w))) / len(w)
            avgs.append(avg)
            
        chosen_indexes = []
        for i in xrange(len(avgs)):
            if avgs[i] > cutoff:
                chosen_indexes.append(i)
        
        
    # setup pylab
    #fig = pylab.figure()    
    pylab.subplot(211)
    pylab.grid(True)
        
    for h in hidden_vars:
        x, y = zip(*h)
        pylab.plot(x, y, '-')
    
    pylab.legend(range(1, len(hidden_vars) + 1))
    
    if weights:
        pylab.subplot(212)
        pylab.grid(True)        
        for i in chosen_indexes:
            x, y = zip(*weights[i])
            pylab.plot(x, y, '-')
        pylab.legend(chosen_indexes)
    
    
    pylab.show()

if __name__ == '__main__':
    main(sys.argv)
