from math import sqrt
from random import uniform
from pylab import plot, figure, show, ion, xlabel, ylabel, title
from datetime import timedelta

from pybrain.datasets import SupervisedDataSet
from pybrain.supervised import BackpropTrainer
from pybrain.structure import SigmoidLayer, LinearLayer, FeedForwardNetwork, FullConnection

variables = ['variance', 'positive variance', 'negative variance']

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

def take(data1, rate = 10, frame = 1):
    '''Data must be in format [(timestamp, reading), ...]'''

    counter = 1
    last = 0
    resp = []

    ##function definition
    #time = lambda x: timedelta(x).total_seconds()

    while counter < len(data1):
        #Make the record of samples
        while (data1[counter][0] - data1[last][0]) < rate and counter < len(data1)-1: 
            counter +=1
        points = [ data1[point] for point in xrange(last, counter +1) ]
        
        #Criate the variables by record
        average = sum( map(lambda x: x[1], points) )/(counter-last+1)
        variance = sqrt( sum([ (point[1]-average)**2 for point in points ])/(counter-last+1) )
#        crec = []
#        dec = []
#        for i in range(len(points)-1):
#            if points[i+1][1] - points[i][1] > 0:
#                crec.append(points[i])
#            else:
#                dec.append(points[i])
#        p_diff = sum([ (crec[i+1][1] - crec[i][1])/(crec[i+1][0] - crec[i][0]) for i in range(len(crec)-1) ])/len(crec)
#        n_diff = sum([ (dec[i+1][1] - dec[i][1])/(dec[i+1][0] - dec[i][0]) for i in range(len(dec)-1) ])/len(dec)
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

        resp.append( {'past': (variance, pos_variance, neg_variance), 'average': average, 'next': next,
                      'delta': delta, 'next_delta': next_delta} )
#        resp.append( {'past': (variance, p_diff, n_diff), 'average': average, 'next': next} )
#        print '.', counter
    return resp

def compare_net_samples(net, data, agreement = 0.5):
    '''@param net is the network, data isn't the dataset, but the list of ((param, param1 ...), output) tuples, agreement is the bound of acceptable difference between output of samples and of net.
       @return returns the agreement as percentage'''
    counter = 0
    n_agree = 0
    r_n_agree = 0
    for i in data:
        guess = net.activate(i['past'])
        out = (i['next'] - i['average'])
        diff = abs(guess - out)
        if diff <= agreement:
            counter +=1
        else:
            n_agree += diff
            if out:
                r_n_agree += diff*100./abs(out)
            else:
                if diff:
                    r_n_agree += 100.
    agreement = counter*100./len(data)
    if counter != len(data):
        print " %2.2f percent of agreement. \n %2.2f not agreement as average.\n%2.2f percent relative not agreement." %( agreement, diff/(len(data) - counter), n_agree/(len(data) - counter) )
    else:
        print "Warning! All points agree!"
    return agreement

def compare_net_samples_long(net, data, agreement = 0.5, steps = 1):
    #Verifying inputs
    if not len(data):
        return None
    if steps > len(data):
        print 'There are more steps than dataset can support'
        steps = len(data)

    #Now we starts
    dummy_point = data[0]['past']
    diff = []

    #defining function
    w_average = lambda n, i,val: (dummy_point[n]*data[i]['delta'] + val * data[i]['next_delta'])/(data[i]['delta']+data[i]['next_delta'])
    for i in range(steps):
        guess = net.activate(dummy_point)
        diff.append(guess - (data[i]['next'] - data[i]['average']))
        if diff[i] > 0:
            dummy_point = (w_average(0,i, guess + data[i]['average']),
                           w_average(1,i, diff[i]),
                           dummy_point[2])
        else:
            dummy_point = (w_average(0,i, guess + data[i]['average']),
                           dummy_point[1],
                           w_average(2,i, -diff[i]  ))


    time_elapsed = 0
    for i in xrange(len(diff)):
        time_elapsed += data[i]['next_delta']
        if time_elapsed >= 3600:
            print 'Error %2.2f%%, %02d:%02d:%02d h after reading.' %(abs(diff[i])*100./data[i]['next'],
                                                                time_elapsed/3600, (time_elapsed%3600)/60, (time_elapsed%60))
        elif time_elapsed >= 60:
            print 'Error %2.2f%%,    %02d:%02d min after reading.' %(abs(diff[i])*100./data[i]['next'],
                                                                (time_elapsed%3600)/60, (time_elapsed%60))
        else:
            print 'Error %2.2f%%,       %2.0f seg after reading.' %(abs(diff[i])*100./data[i]['next'], time_elapsed)

def make_data(f_file, n_motes, rating = 10, prevision = 10):
    '''This is especific for us problem, n_motes is the number of motes in file, rating is the tame in past that I can see.
        this returns a tuple as (timestamp, reading)'''
    try:
        f_reading = open(f_file, 'r')
        data = []

        for line in f_reading:
            line = line.split()
            data.append( (float(line[0]), float(line[-1])) )

        #function
        data_module = lambda x: map( lambda z: data[z], filter( lambda y: y% n_motes == x, xrange(len(data)) ) )

        data1 = data_module(0)
        return take(data1, rate = rating, frame = prevision)
    except IOError:
        print 'Invalid File'
        return []
    finally:
        f_reading.close()

def main(f_samples):
    f_reading = open(f_samples, 'r')
    global data
    data = []

    for line in f_reading:
        line = line.split()
        data.append( (float(line[0]), float(line[-1])) )

    #function
    data_module = lambda x: map( lambda z: data[z], filter( lambda y: y% 5 == x, xrange(len(data)) ) )

    global data1
    data1 = [data_module(0), data_module(1), data_module(2), data_module(3), data_module(4)]

    global data_transformed
    data_transformed = take(data, rate = 60)

    global data_transformed_training
    data_transformed_training = map( lambda x: data_transformed[x], filter( lambda x: uniform(0, 1) > 0.3, xrange(len(data_transformed)) ))

    #Learning process-----------------------------------------------------------------

    global net, samples, trainer
    net = FeedForwardNetwork()
    inLayer = LinearLayer(3)
    hiddenLayer0 = SigmoidLayer(1)
    hiddenLayer1 = SigmoidLayer(3)
    outLayer = LinearLayer(1)

    net.addInputModule(inLayer)
#    net.addModule(hiddenLayer0)
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

    for i in data_transformed_training:
        samples.addSample(i['past'], i['next'] - i['average'])
    trainer = BackpropTrainer(net, samples)

    print 'Training'
    trainer.trainUntilConvergence(maxEpochs= 10)

    print 'Comparing'
    compare_net_samples(net, data_transformed)
    print "Number of samples %d for training." %len(data_transformed_training)

if __name__ == '__main__':
    from sys import argv
    if len(argv) < 2:
        '''Usage python %s [name_of_samples_file]''' %argv[0]
        argv.append('readings_27_04_12_15h22m53s.txt')
    print 'Working over', argv[1]

    #from pybrain.tools.shortcuts import buildNetWork
    
    main(argv[1])
