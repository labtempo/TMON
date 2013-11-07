#@author Breno W. Carvalho

from math import sqrt
from random import uniform
from pylab import plot, plot_date, figure, date2num, ion, ioff, legend, show, xticks
from datetime import timedelta, datetime

from pybrain.datasets import SupervisedDataSet
from pybrain.supervised import BackpropTrainer
from pybrain.structure import SigmoidLayer, LinearLayer, FeedForwardNetwork, FullConnection

import os, pickle

class Forecaster():
    '''
    Forecaster encapsulates the generic concept of a forecaster.
    To use it you must initialize it with an predict function, what will recive points of data and the lag as arguments.
    The function learn recive an data set and lag, it is used by some forecasts algorithms.
    You also can use the default forecaster generators rather then implementing yours.
    '''
    def __init__(self, name= 'Forecaster', learn_function = lambda x, y, z: None, predict_function = lambda x, y: None,
                 update_function = lambda x, y: None, restart_function = None):
        self.name = str(name)
        self.initialized = False

        self.learn = lambda data, lag: learn_function(self, data, lag)
        self.predict = lambda lag: predict_function(self, lag)
        self.update = lambda data: update_function(self, data)
        if not restart_function:
            def restart_function(self):
                self.initialized = False
        self.restart = lambda: restart_function(self)
#---

def make_graph(*args):
    '''Each argument must be in this format {'x':[...], 'y':[...]}'''
    import matplotlib.patches as patches
    from matplotlib.path import Path
    fig = figure()
    ax = fig.add_subplot(111)
    ion()
    ax.grid(True)
    ax.set_title('Thermal Forecasts')
    ax.set_ylabel('Celsius degrees')
    ax.set_xlabel("Time")


    for i in args:
        #dates = [datetime.fromtimestamp(ts) for ts in i['x']]
        if 'learning_bounds' in i.keys():
            rect = patches.PathPatch(Path(i['learning_bounds']),
                                     facecolor = i['color'], lw = 0, alpha = 0.40)
            ax.add_patch(rect)
        plot(i['x'], i['y'], color = i['color'], marker = '', linestyle = i.get('linestyle', '--'), label=i['name'])
    locs, labels = xticks()
    xticks(locs, map(lambda x:  datetime.fromtimestamp(x), locs))
    legend()
    show()
    ioff()

#---

def read_data(f_reading):
    '''This is especific for our problem, n_motes is the number of motes in file, rating is the passed time that I can see.
        Returns a dictionary of dictionaries, the former is a collection of readings divided by mote, the second is the same but convertered for learning algorithm, e.g:
        'data': {'255':[(0, 0),(1, 1.75),(2, 3)], '254': [(3, 2.55),(4, 6),(5, 7)]}'''
    '''
    data = {}
    for i in range(5):
        data[str(i)] = [ (i, uniform(10, 15)*i/100) for i in range(100, int(uniform(200,300)))]
    return data
    '''
    try:
        print 'Making data'
        elapsed = os.times()[-1]
        from SharedLibs.tracetools import TraceReader, TraceAdapter, UNIFORM_FILE_FORMAT
        data = {}
        tR = TraceReader(f_reading, motes_to_ignore = [236, 246])
        tA = TraceAdapter(tR, UNIFORM_FILE_FORMAT)

        for momment in tA.parse():
            timestamp = momment['timestamp']
            for mote in momment.keys()[1:]:
                if mote in data.keys():
                    data[mote].append((timestamp, momment[mote]))
                else:
                    data[mote] = [(timestamp, momment[mote])]

        for mote in data:
            i, j = 0, 0
            while j < len(data[mote]):
                while j < len(data[mote]) and data[mote][i][0] == data[mote][j][0]:
                    j +=1
                if i != j:
                    data[mote][i:j] = [(data[mote][i][0], sum(map(lambda x: x[1], data[mote][i:j]))/(j-i))]
                i +=1
                j = i
        elapsed = os.times()[-1] - elapsed
        print '\tData done in %d seconds.\n\tMotes %s' %(elapsed, repr(data.keys())[1:-1])
        #save = open(f_reading+'data', 'w')
        #pickle.dump(data, save)
        #save.close()
        return data

    except IOError:
        print 'Invalid File'
        return {}
#'''
#---

def generate_naive_forecaster():
    def predict(self, lag):
        return self.mem[1]
    def update(self, data):
        self.mem = data
        self.initialized = True
        
    return Forecaster(name = 'Naive', predict_function = predict, update_function= update)

#---

def generate_constant_forecaster(value = 0):
    def predict(self, lag):
        return self.mem[1]

    const = Forecaster(name = 'Constant', predict_function = predict)
    const.mem = [None, value]
    return const

#---

def generate_exp_means_forecaster(alpha = 0.3):
    def predict(self, lag):
        if self.initialized:
            return self.mem
        else:
            raise Exception("Forecaster "+self.name+" don't initialized.")

    def update(self, data):
        if self.initialized:
            self.mem = self.alpha*data[1] + (1-self.alpha)*self.mem
        else:
            self.mem = data[1]
            self.initialized = True

    exp = Forecaster(name = 'Exponential', predict_function = predict, update_function = update)
    exp.alpha = 0.5
    return exp

#---

def generate_holts_linear_forecaster(alpha = 0.5, beta = 0.3):
    def predict(self, lag):
        if self.initialized:
            return self.L + self.b*lag
        else:
            raise Exception("Forecaster "+self.name+" don't initialized.")

    def update(self, data):
        if not self.initialized:
            self.L = data[1]
            self.b = 0
            self.initialized = True
        else:
            self.L = self.alpha*(data[1]) + (1 - self.alpha)*(self.L + self.b)
            self.b = self.alpha*(data[1] - self.L) + (1 - self.alpha)*(self.b)
            self.initialized = True

    holtsLinear = Forecaster(name = "Holt's linear", predict_function = predict, update_function = update)
    holtsLinear.alpha = alpha
    holtsLinear.beta  = beta
    return holtsLinear

#---

def generate_network_forecaster(history_size = 1):
    #Building Network proccess-------------------------------------------------------
    net = FeedForwardNetwork()
    inLayer = LinearLayer(history_size)
    hiddenLayer0 = SigmoidLayer(history_size)
    hiddenLayer1 = LinearLayer(3)
    outLayer = LinearLayer(1)

    net.addInputModule(inLayer)
    net.addModule(hiddenLayer0)
    net.addModule(hiddenLayer1)
    net.addOutputModule(outLayer)

    net.addConnection(FullConnection(inLayer, hiddenLayer0))
    #net.addConnection(FullConnection(inLayer, outLayer))
    #net.addConnection(FullConnection(hiddenLayer0, outLayer))
    net.addConnection(FullConnection(hiddenLayer0, hiddenLayer1))
    net.addConnection(FullConnection(hiddenLayer1, outLayer))
    net.sortModules()
    AUX = 0.1
    print net
    ##Net with 3 inputs, 8 hidden neurons in a layer and 8 in another, and 1 out.
    #net = buildNetwork(3,8,8,1)

    #Making Forecaster---------------------------------------------------------------    
    def learn(self, data, lag, epoch = 60):
        self.samples.clear()
        self.true_predictions = 0 #This numbers indicates how long the net was used to predict a event rather than using another method because haven't enought data.
        self.predictions = 0
        self.lag = lag
        for i in range( len(data) - (lag + self.history_size) ):
            self.samples.addSample([data[j][1]*AUX for j in range(i, i + self.history_size)], data[i + lag + self.history_size][1]*AUX)
        print 'Training'
 
        elapsed = os.times()[-1] #take time as miliseconds
        self.trainer.trainUntilConvergence(maxEpochs = epoch)# , validationProportion = 0.01)
        elapsed = os.times()[-1] - elapsed

        if elapsed <= 60:
            time = '%2.1f seconds.' %elapsed
        elif elapsed <= 3600:
            time = '%d minutes and %2.1f seconds.' %(elapsed/60, elapsed%60)
        else:
            time = '%d hours, %d minutes and %2.1f seconds.' %(elapsed/3600, elapsed/60, elapsed%60)
        print 'Trained along', time

    def predict(self, lag):
        if self.initialized:
            return self.mem
        else:
            if 'vect' in dir(self):
                return self.vect[-1]
            else:
                raise Exception("Forecaster "+self.name+" don't initialized.")

    def update(self, data):
        if self.initialized:
            self.vect.append(data[1])
            if len(self.vect) > self.history_size:
                self.vect = self.vect[1:]
            self.mem = self.net.activate(map(lambda x: x*AUX, self.vect))*(1/AUX)
        else:
            self.mem = data[1]
            if 'vect' in dir(self):
                self.vect.append(data[1])
            else:
                self.vect = [data[1]]
            if len(self.vect) >= self.history_size:
                self.initialized = True

    NN = Forecaster(name = 'Neural Net', predict_function = predict, update_function = update, learn_function = learn)
    NN.history_size = history_size
    NN.net = net
    NN.samples = SupervisedDataSet(history_size,1)
    NN.trainer = BackpropTrainer(NN.net, NN.samples)
    return NN
#---

def analyse_forecaster(forecaster, data, data_for_learning = None, delta = 60, lag = 10, train = False, verbose = False, return_points = False, color = 'b'):
    mse = mae = me = 0

    if return_points:
        points = {'x':[], 'y':[], 'name': forecaster.name, 'color': color}

    if train:
        forecaster.learn(data = [data_for_learning[i]
                         for i in filter(lambda x: not x%delta, range(len(data_for_learning)))], lag = lag)
        #Used to draw the rectangles of training on graph
        if return_points and data_for_learning:
            dy = map(lambda x: x[1], data_for_learning)
            dYmin, dYmax = min (dy), max (dy)
            dXmin, dXmax = data_for_learning[0][0], data_for_learning[-1][0]

            points['learning_bounds'] = [(dXmin, dYmin), (dXmax, dYmin), (dXmax, dYmax), (dXmin, dYmax)]
    i = 0
    lenght = (len(data) - lag) / delta

    if not lenght:
        raise Exception("Data doesn't satisfies constraints.")
    while i  < lenght:
        forecaster.update(data[i*delta])
        guess = forecaster.predict(lag)#net.activate(i['past'])
        out = data[i*delta+lag][1]
        diff = guess - out
        if return_points:
            points['x'].append(data[i*delta+lag][0]) #timestamp
            points['y'].append(guess) #value of forecast

        if verbose:
            print guess

        mse += diff**2
        mae += abs(diff)
        me  += diff
        i   += delta
    if verbose:
        print 'Forecaster Data:', len(points['x'])

    mse /= lenght
    mae /= lenght
    me  /= lenght
    print forecaster.name+':'
    print '\tMSE: %4.6f \tMAE: %4.6f \tME:  %4.6f' % (mse, mae, me)
    out = {'mse': mse, 'mae': mae, 'me': me}
    if return_points:
        out['points'] = points
    return out

#---

def main(f_in, minimum = 10, LAG = 10, l_interval = 0.05):
    
    try:
        readings = open(f_in+'data', 'r')
        print('Reading data')
        data = pickle.load(readings)
        print('Data completely read')
        readings.close()
    except:
        data = read_data(f_in)

    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    import matplotlib.patches as patches

    for mote in data:
        print '\nMote:', mote
        if len(data[mote]) > minimum:
            const = generate_constant_forecaster( value = sum(map(lambda x: x[1], data[mote]))/len(data[mote]) )
            naive = generate_naive_forecaster()
            exp = generate_exp_means_forecaster()
            holts = generate_holts_linear_forecaster()
            #net = generate_network_forecaster(history_size = 3)

            L_I = int(l_interval*len(data[mote]))

            samples = {'x': map(lambda x: x[0], data[mote]), 'y': map(lambda x: x[1], data[mote]),
                       'name': 'Observation', 'color': 'k', 'linestyle': '-'}

            #Below we analyse each forecaster, then whe plot a graph of them.
            make_graph(samples,
                       analyse_forecaster(const, data[mote], return_points = True, lag = LAG, color = 'm')['points'],
                       analyse_forecaster(naive, data[mote], return_points = True, lag = LAG, color = 'm')['points'],
                       analyse_forecaster(exp,   data[mote], data[mote][0:L_I],
                                          train = True, return_points= True, lag = LAG, color = 'g')['points'],
                       analyse_forecaster(holts, data[mote], return_points = True, lag = LAG,  color = 'b')['points'])#,
            #           analyse_forecaster(net,   data[mote], data[mote][0:L_I/4],
            #                              train = True, return_points = True, lag = LAG,  color = 'r')['points'],
            #           analyse_forecaster(net,   data[mote], data[mote][0:L_I/2],
            #                              train = True, return_points = True, lag = LAG,  color = '#FFA500')['points'],
            #           analyse_forecaster(net,   data[mote], data[mote][0:L_I*3/4],
            #                              train = True, return_points = True, lag = LAG,  color = '#FF8C00')['points'],
            #           analyse_forecaster(net,   data[mote], data[mote][0:L_I],
            #                              train = True, return_points = True, lag = LAG,  color = '#FF6347')['points'])
            #print net.net.params
            raw_input()
            print '#-------------------------------------#'

#---

if __name__ == '__main__':
    from sys import argv
    if len(argv) < 2:
        print 'Usage: python %s {file for training} [least number of samples] [lag]' %argv[0]
        exit(-1)
    if len(argv) >= 4:
        main(argv[1], int(argv[2]), int(argv[3]))
    main(argv[1])
