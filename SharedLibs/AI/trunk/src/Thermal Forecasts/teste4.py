from math import sqrt
from random import uniform
from pylab import plot, figure, show, ion, xlabel, ylabel, title
from datetime import timedelta

from pybrain.datasets import SupervisedDataSet
from pybrain.supervised import BackpropTrainer
from pybrain.structure import SigmoidLayer, LinearLayer, FeedForwardNetwork, FullConnection

variables = ['variance', 'positive variance', 'negative variance']

class Forecaster():
    def __init__(self, name= 'Forecaster', learn_function = None, predict_function = None):
        self.name = str(name)
        self.learn = learn_function
        self.predict = predict_function

def to_plot(d,x = 0, y = 1, noise = 2):
    figure()
    xlabel('X = %s' %variables[x])
    ylabel('Y = %s' %variables[y])
    title("Separability's graphic, noise is about %2.1f.\nBlues are ups and reds are downs, yellows are noise"% noise)
    for i in d:
        if abs(i['next'] - i['average']) < noise:
            plot(i['past'][x], i['past'][y], 'sy')
        elif i['next'] < i['average']:
            plot(i['past'][x], i['past'][y], 'r^')
        else:
            plot(i['past'][x], i['past'][y], 'bo')
    ion()
    show()

def take(data1, pos = 0, rate = 10, frame = 1):
    '''Data must be in format [(timestamp, reading), ...]'''

    counter = pos+1
    last = pos
    #Make the record of samples
    while (data1[counter][0] - data1[last][0]) < rate and counter < len(data1)-1: 
        counter +=1
    points = [ data1[point] for point in xrange(last, counter +1) ]
    
    #Criate the variables by record
    average = sum( map(lambda x: x[1], points) )/(counter-last+1)
    variance = sqrt( sum([ (point[1]-average)**2 for point in points ])/(counter-last+1) )
    #crec = []
    #dec = []
    #for i in range(len(points)-1):
        #if points[i+1][1] - points[i][1] > 0:
            #crec.append(points[i])
        #else:
            #dec.append(points[i])
    #p_diff = sum([ (crec[i+1][1] - crec[i][1])/(crec[i+1][0] - crec[i][0]) for i in range(len(crec)-1) ])/len(crec)
    #n_diff = sum([ (dec[i+1][1] - dec[i][1])/(dec[i+1][0] - dec[i][0]) for i in range(len(dec)-1) ])/len(dec)
    pos_variance = sqrt( sum([ (point[1]-average)**2 for point in filter( lambda x: x[1] > average, points ) ])/len(points) )
    neg_variance = sqrt( sum([ (point[1]-average)**2 for point in filter( lambda x: x[1] < average, points ) ])/len(points) )

    delta = points[-1][0]-points[1][0]
    #Walk a little bit to make de 'future' frame
    last = counter
    while timedelta(data1[counter][0] - data1[last][0]).total_seconds() < frame and counter < len(data1)-1:
        counter += 1
    next = sum( [data1[i][1] for i in xrange(last, counter+1)] )/(counter-last+1)

    next_delta = points[-1][0]-points[1][0]
    last = counter
    counter += 1

    return {'past': (variance, pos_variance, neg_variance), 'average': average, 'next': next,
                  'delta': delta, 'next_delta': next_delta}
    #resp.append( {'past': (variance, p_diff, n_diff), 'average': average, 'next': next} )
    #print '.', counter

def compare_forecaster_samples(forecaster, data, agreement = 0.5):
    '''@param net is the network, data isn't the dataset, but the list of ((param, param1 ...), output) tuples, agreement is the bound of acceptable difference between output of samples and of net.
       @return returns the agreement as percentage'''
    mse = 0
    mae = 0
    me  = 0
    for i in range(len(data)):
        guess = forecaster.predict(data[i][0])#net.activate(i['past'])
        out = data[i][1]
        diff = guess - out
        mse += diff**2
        mae += abs(diff)
        me  += diff
    mse /= len(data)
    mae /= len(data)
    me  /= len(data)
    print forecaster.name+':'
    print '\tMSE: %4.3f \tMAE: %4.3f \tME:  %4.3f' % (mse, mae, me)
    return mse

def read_data(f_reading, rating = 10, prevision = 10):
    '''This is especific for us problem, n_motes is the number of motes in file, rating is the tame in past that I can see.
        this returns a tuple as (timestamp, reading)'''
    try:
        data = []
        last = -1
        for line in f_reading:
            line = line.split()
            if line[0] != last:
                data.append( (float(line[0]), float(line[-1])) )
            last = line[0]
        print 'Making data'
        return data, [take(data, pos = d, rate = rating, frame = prevision) for d in range(1000)]
    except IOError:
        print 'Invalid File'
        return []
    finally:
        f_reading.close()

def generate_forecasters(data,dtt, alpha):
    #Learning process-----------------------------------------------------------------
    global net, samples, trainer
    net = FeedForwardNetwork()
    inLayer = LinearLayer(3)
    hiddenLayer0 = SigmoidLayer(1)
    hiddenLayer1 = SigmoidLayer(3)
    outLayer = LinearLayer(1)

    net.addInputModule(inLayer)
    net.addModule(hiddenLayer0)
#    net.addModule(hiddenLayer1)
    net.addOutputModule(outLayer)

#    net.addConnection(FullConnection(inLayer, hiddenLayer0))
    net.addConnection(FullConnection(inLayer, outLayer))
#    net.addConnection(FullConnection(hiddenLayer0, outLayer))
#    net.addConnection(FullConnection(hiddenLayer0, hiddenLayer1))
#    net.addConnection(FullConnection(hiddenLayer1, outLayer))
    net.sortModules()
    print net
    ##Net with 3 inputs, 8 hidden neurons in a layerand 8 in another, and 1 out.
    #net = buildNetwork(3,8,8,1)
    ##Set with 2 inputs and one output for each sample
    samples = SupervisedDataSet(3,1)

    for i in dtt:
        samples.addSample(i['past'], i['next'] - i['average'])
    trainer = BackpropTrainer(net, samples)

    print 'Training'
    #trainer.trainUntilConvergence(maxEpochs= 1)

    #Making Forecasters---------------------------------------------------------------
    aux = map(lambda x: x[0], data)
    def exp(self, a, x):
        self.exp = a* data[aux.index(x)-1][1] + (1-a)*self.exp
        return self.exp

    naive = Forecaster(name= 'Naive', predict_function = lambda x: data[aux.index(x)-1][1])
    exponential = Forecaster(name= 'Exponential')
    exponential.exp = data[0][1]
    exponential.predict = lambda x: exp(exponential, alpha, x)
    network = Forecaster(name= 'Network', predict_function = net.activate)

    return naive, exponential, network
    
def main(f_samples):
    f_reading = open(f_samples, 'r')
    global data, data_transformed
    data, data_transformed = read_data(f_reading, rating = 60, prevision = 10)
    print 'Lenght of data set:', len(data)
    global data_transformed_training
    data_transformed_training = map( lambda x: data_transformed[x], filter( lambda x: uniform(0, 1) > 0.3, xrange(len(data_transformed)) ))

    #Comparing step-------------------------------------------------------------------
    print 'Comparing'
    naive, exponential, network = generate_forecasters(data, data_transformed_training, 0.1)
    compare_forecaster_samples(naive, data[:2000])
    compare_forecaster_samples(exponential, data[:2000])
    #compare_forecaster_samples(network, data)
#    print "Number of samples %d for training." %len(data_transformed_training)

if __name__ == '__main__':
    from sys import argv
    if len(argv) < 2:
        '''Usage python %s [name_of_samples_file]''' %argv[0]
        argv.append('readings_27_04_12_15h22m53s.txt')
    print 'Working over', argv[1]
    
    main(argv[1])
