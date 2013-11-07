#@author Breno W. Carvalho

from math import sqrt
from random import uniform
from pylab import plot, plot_date, figure, grid, show, ion, ioff, xlabel, ylabel,legend, title
from datetime import timedelta

from pybrain.datasets import SupervisedDataSet
from pybrain.supervised import BackpropTrainer
from pybrain.structure import SigmoidLayer, LinearLayer, FeedForwardNetwork, FullConnection

class Forecaster():
    '''functions:
            predict argments are just a tuple representing a point of forecaster's domain
            learn arguments is the training set, in format[ (point, output), ...]'''
    def __init__(self, name= 'Forecaster', learn_function = lambda x: None, predict_function = lambda x: None):
        self.name = str(name)
        def learn(data):
            return learn_function(self, data)
        self.learn = learn
        def predict(data):
            return predict_function(self, data)
        self.predict = predict
        self.initialized = False
#---

def make_graph(*args):
    '''Each argument must be as this format {'x':[...], 'y':[...]}'''
    import matplotlib.patches as patches
    from matplotlib.path import Path
    fig = figure()
    ion()
    grid = True
    title = 'Thermal Forecasts'
    ylabel = 'Celsius degrees'
    for i in args:
        plot(i['x'], i['y'], color = i['color'], linestyle = i.get('linestyle', '--'), label=i['name'])
        if 'learning_bounds' in i.keys():
            ax = fig.add_subplot(111)
            rect = patches.PathPatch(Path(i['learning_bounds']),
                                     facecolor = i['color'], lw = 0, alpha = 0.40)
            ax.add_patch(rect)
    legend()
    show()
    ioff()

def read_data(f_reading, rating = 10, prevision = 10, percent_for_learning = 0.7):
    '''This is especific for us problem, n_motes is the number of motes in file, rating is the tame in past that I can see.
        Returns a dictionary of dictionaries, the former is a collection of readings divided by mote, the second is the same but convertered for learning algorithm, e.g:
        { 'data': {'255':[(0, 0),(1, 1.75),(2, 3)], '254': [(3, 2.55),(4, 6),(5, 7)]},
          'data_for_learning': {'255':[(0,43, 1)], '254':[(7.8, 8)]} }'''
    try:
        data = {}
        last = -1
        for line in f_reading:
            line = line.split()
            if not line[1] in data:
                data[line[1]] = []
            data[line[1]].append( (float(line[0]), float(line[-1])))

        for mote in data:
            j = 0
            i = 1
            while( i <= len(data[mote])):
                if i == len(data[mote]) or data[mote][i][0] != data[mote][j][0]:
                    if i > j+1:
                        data[mote][j:i] = [ ( data[mote][j][0],
                                          sum(map(lambda x: x[1], data[mote][j:i]))/(i-j) ) ] #sum of tuples
                    j += 1
                    i = j+1
                else:
                    i +=1   

        print 'Making data'
        #data_for_learning = {l:[preprocessing_learning(data[l], pos = d, frame_past = rating, frame_after = prevision)
         #                   for d in range(len(data[l])-1)] for l in data}
        #for mote in data_for_learning:
        #    data_for_learning[mote] = filter (lambda x: uniform(0,1) <= percent_for_learning, data_for_learning[mote])
        #return {'data': data, 'data_for_learning': data_for_learning }
        return data

    except IOError:
        print 'Invalid File'
        return []
        #return {}, {}
    finally:
        f_reading.close()

#---

def generate_perfect_forecaster():
    def p(self, point):
        '''Point must be a tuple (input, output).'''
        return point[1]
    return Forecaster(name = 'Magic', predict_function = p)

def generate_naive_forecaster():
    def naive(self, point):
        '''Point must be a tuple (input, output).'''
        if self.initialized:
            resp = self.last
            self.last = point[1]
        else:
            resp = self.last = point[1]
            self.initialized = True
        return resp
    return Forecaster(name = 'Naive', predict_function = naive)

def generate_exp_means_forecaster(alpha = 0.3):
    '''Point must be a tuple (input, output).'''
    def exp(self, point):
        if self.initialized:
            out = self.exp
            self.exp = self.alpha*point[1] + (1-self.alpha)*self.exp
        else:
            out = self.exp = point[1]
            self.initialized = True
        return out
    exponential = Forecaster(name= 'Exponential', predict_function = exp)
    exponential.alpha = alpha
    return exponential

def generate_holts_linear_forecaster(alpha = 0.5, beta = 0.5, m = 1):
        def holts(self, point):
            if not self.initialized:
                self.L = point[1]
                self.b = 0
                self.initialized = True
                return self.L
            Lt = alpha*(point[1]) + (1- alpha)*(self.L + self.b)
            bt = alpha*(Lt- self.L) + (1- alpha)*(self.b)
            self.L = Lt
            self.b = bt
            return Lt + bt
        holtsLinear = Forecaster(name="Holt's linear", predict_function = holts)
        holtsLinear.alpha = alpha
        holtsLinear.beta  = beta
        return holtsLinear
    

def generate_network_forecaster(history_size = 1):
    #Building Network proccess-------------------------------------------------------
    net = FeedForwardNetwork()
    inLayer = LinearLayer(history_size)
    hiddenLayer0 = LinearLayer(1)
    #hiddenLayer1 = SigmoidLayer(3)
    outLayer = LinearLayer(1)

    net.addInputModule(inLayer)
    net.addModule(hiddenLayer0)
    #net.addModule(hiddenLayer1)
    net.addOutputModule(outLayer)

    net.addConnection(FullConnection(inLayer, hiddenLayer0))
    #net.addConnection(FullConnection(inLayer, outLayer))
    net.addConnection(FullConnection(hiddenLayer0, outLayer))
    #net.addConnection(FullConnection(hiddenLayer0, hiddenLayer1))
    #net.addConnection(FullConnection(hiddenLayer1, outLayer))
    net.sortModules()
    print net
    ##Net with 3 inputs, 8 hidden neurons in a layerand 8 in another, and 1 out.
    #net = buildNetwork(3,8,8,1)

    #Making Forecaster---------------------------------------------------------------    
    def learn_net(self, data, epoch = 10):
        self.samples.clear()
        self.true_predictions = 0 #This numbers indicates how long the net was used to predict a event often uses another method because haven't enought data.
        self.predictions = 0
        for i in range(len(data)-self.history_size-1):
            self.samples.addSample([data[j][1]*.1 for j in range(i, i + self.history_size)], data[i + self.history_size][1]*.1)
        print 'Training'

        import os
        elapsed = os.times()[-1]
        self.trainer.trainUntilConvergence(maxEpochs = epoch)
        elapsed = os.times()[-1] - elapsed

        if elapsed <= 60:
            time = '%2.1f seconds.' %elapsed
        elif elapsed <= 3600:
            time = '%d minutes and %2.1f seconds.' %(elapsed/60, elapsed%60)
        else:
            time = '%d hours, %d minutes and %2.1f seconds.' %(elapsed/3600, elapsed/60, elapsed%60)
        print 'Trained along', time

    def predict_net(self, point):
        if not self.initialized:
            if not 'last' in dir(self):
                self.last = [point]
            else:
                self.last.append(point)
            self.initialized = len(self.last) >= self.history_size
            return point[1]
        net_out = self.net.activate(map( lambda x: x[1], self.last))
        del(self.last[0])
        self.last.append(point)
        return float(net_out)

    #-------------------------------------------
    
    network = Forecaster(name= 'Network', learn_function = learn_net, predict_function = predict_net)
    network.net = net
    network.samples = SupervisedDataSet(history_size,1)
    network.history_size = history_size
    network.trainer = BackpropTrainer(network.net, network.samples)
    #---------------------------------------------------------------------------------

    return network

#---

def compare_forecaster(forecaster, data, data_for_learning = None, train = False, verbose = False, return_points = False, color = 'b'):
    mse = 0
    mae = 0
    me  = 0
    if return_points:
        points = {'x':[], 'y':[], 'name': forecaster.name, 'color': color}
    if train:
        forecaster.learn(data_for_learning)
        if return_points and data_for_learning:
            d = data_for_learning
            dy = map(lambda x: x[1], d)
            dmin, dmax = min (dy), max (dy)
            points['learning_bounds'] = [(d[0][0],dmin), (d[-1][0],dmin), (d[-1][0], dmax), (d[0][0], dmax)]

    for i in range(len(data)):
        guess = forecaster.predict(data[i])#net.activate(i['past'])
        out = data[i][1]
        diff = guess - out
        if return_points:
            points['x'].append(data[i][0])
            points['y'].append(guess)
        if verbose:
            print guess
        mse += diff**2
        mae += abs(diff)
        me  += diff
    mse /= len(data)
    mae /= len(data)
    me  /= len(data)
    print forecaster.name+':'
    print '\tMSE: %4.6f \tMAE: %4.6f \tME:  %4.6f' % (mse, mae, me)
    if return_points:
        return mse, points
    return mse

def main(f_in, minimum = 10):
    data = read_data(open(f_in, 'r'))
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    import matplotlib.patches as patches

    for mote in data:
        print '\nMote:', mote
        if len(data[mote]) > minimum:
            naive = generate_naive_forecaster()
            exp = generate_exp_means_forecaster()
            holts = generate_holts_linear_forecaster()
            net = generate_network_forecaster(1)
            
            samples = {'x': map(lambda x: x[0], data[mote]), 'y': map(lambda x: x[1], data[mote]),
                       'name': 'Observation', 'color': 'k', 'linestyle': '-'}
            make_graph(samples,
                       compare_forecaster(naive, data[mote], return_points= True, color = 'm')[1],
                       compare_forecaster(exp,   data[mote], return_points= True, color = 'g')[1],
                       compare_forecaster(holts, data[mote], return_points= True, color = 'b')[1],
                       compare_forecaster(net,   data[mote], data[mote][2:1000],
                                          train = True, return_points= True, color = 'r')[1],
                       compare_forecaster(net,   data[mote], data[mote][2:2000],
                                          train = True, return_points= True, color = '#FFA500')[1],
                       compare_forecaster(net,   data[mote], data[mote][2:3000],
                                          train = True, return_points= True, color = '#FF8C00')[1],
                       compare_forecaster(net,   data[mote], data[mote][2:4000],
                                          train = True, return_points= True, color = '#FF6347')[1])
            #print 'Predictions really made by network was', net.true_predictions
            raw_input()
            print '#-------------------------------------#'

if __name__ == '__main__':
    from sys import argv
    if len(argv) < 2:
        print 'Usage: python %s [file for training]' %argv[0]
        exit(-1)
    main(argv[1])
