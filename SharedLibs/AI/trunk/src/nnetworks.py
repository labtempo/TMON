'''
This module aims to be a kind of adapter of all kinds of neural networks used in that project.
It may be incomplete and may change over time.
'''

import neurolab as _nl
import numpy as _np
import random
from pybrain.tools import shortcuts as _shortcuts
from pybrain import datasets as _datasets
from pybrain.supervised import BackpropTrainer as _BackpropTrainer
    

class AbstractFeedFowardNetWork:
    '''It is an abstract class that is used to design a standard design for all kinds of feedfoward neural networks in this module.'''

    def __init__(self, input_size, topology):
        '''
        @param input_size is the cardinality (lenght) of the input vector
        @param topology, for a feedfoward network, is a list of integers that represents the quantities of each layer.
        The first quantity defines the input layer and the last one the output layer.
        Different kinds of networks may need differents kinds of topology representation
        '''
        pass
    def clearDataSet(self):
        '''That function reset the dataset, but doesn't change the networks current state.'''
        pass
    def addEntriesToDataSet(self, info_array):
        '''@param info_array must be a sequence of tuples [input, target]'''
        pass
    def removeOldestEntriesFromDataSet(self, quantity):
        '''It removes 'quantity' entries from the data set, starting from the oldest one.'''
        pass
    def removeRandomEntriesFromDataSet(self, quantity):
        '''It randomly removes 'quantity' entries from the data set.'''
        pass
    def limitDatasetSize(self, value):
        '''Value represent the maximum size for the data set, if value is equals to None there will not have a quantity limit.'''
        pass
    def trainNetwork(self, maxEpochs):
        '''
        Trains the network using the defined training algorithm.
        @param maxEpochs defines how many times at most we run the training algorith throughout the dataSet. None means no limit.
        '''
        pass
    def setLearningRate(self, value):
        '''@param value must be in [0, 1].'''
        pass
    def getDatasetLength(self):
        pass
    def activateNetwork(self, value):
        '''
        @param value must be like [input, output].
        Returns the output of the network for value as a sample. Recurrent networks have memory so the sample's order matters.
        '''
        pass


class PyBrainFeedFowardFullConectedNetwork(AbstractFeedFowardNetWork):
    '''
    It is an feedfoward full connected (all nodes from one layer are connected to all other nodes from the next layer) network.
    Pybrain still chooses random weights for the conections.
    '''

    def __init__(self, input_size, topology):
        topology = list(topology)+[1]
        self._net     = _shortcuts.buildNetwork(*([input_size]+topology)) #This is used because buildNetwork expects many arguments
        self._data    = _datasets.SupervisedDataSet(topology[0], topology[-1])
        self._data_source = {'inp':_np.array([]),'tar':_np.array([])}        
        self._samples_limit = None
        
        new_params = _np.array([1./ input_size] * len(self._net.params))
        self._net._setParameters(new_params)
        
        self._net.sortModules()

    def clearDataSet(self):
        del(self._data_source)
        self._data_source = {'inp':_np.array([]),'tar':_np.array([])}
        self._data.clear()

    def _update_dataset(self):
        self._data.clear()
        self._data.setField('input', self._data_source['inp'])
        self._data.setField('target', self._data_source['tar'])

    def addEntriesToDataSet(self, info_array):
        '''
        Pybrain add some aditional entries some times for optimization.
        @param info must be a tuple (input_values, output_values) where, input_values and output_values are also tuples (or lists).
        '''
        data_size = len(self._data['input'])
        self._data_source['inp'].resize([data_size+len(info_array), self._net.indim], refcheck = False)
        self._data_source['tar'].resize([data_size+len(info_array), self._net.outdim], refcheck = False)

        for i in xrange(len(info_array)):
            self._data_source['inp'][data_size + i] += info_array[i][0]
            self._data_source['tar'][data_size + i] += info_array[i][1]
        if self._samples_limit != None:
            extra_space = self.getDatasetLength() - self._samples_limit
            if extra_space > 0:
                self.removeOldestEntriesFromDataSet(extra_space)
        self._update_dataset()

    def removeOldestEntriesFromDataSet(self, quantity):
        datasetSize = self.getDatasetLength()
        if datasetSize <= quantity:
            self.clearDataSet()
            return
        self._data_source['inp'] = _np.delete(self._data_source['inp'], xrange(quantity), 0)
        self._data_source['tar'] = _np.delete(self._data_source['tar'], xrange(quantity), 0)
        self._update_dataset()

    def removeRandomEntriesFromDataSet(self, quantity):
        datasetSize = self.getDatasetLength()

        if datasetSize <= quantity:
            self.clearDataSet()
            return
        randomList = _random.sample(xrange(datasetSize), quantity)
        self._data_source['inp'] = _np.delete(self._data_source['inp'], randomList, 0)
        self._data_source['tar'] = _np.delete(self._data_source['tar'], randomList, 0)
        self._update_dataset()


    def limitDatasetSize(self, value):
        self._samples_limit = value
        if value != None:
            assert value >= 0, 'That value must be positive!'

    def trainNetwork(self, maxEpochs = 100):
        self._trainer.trainEpochs(epochs = maxEpochs)

    def setLearningRate(self, value):
        self._learning_rate = float(value)
        assert 0 <= self._learning_rate <= 1, 'Learning rate must be between 0 and 1'
        self._trainer = _BackpropTrainer(self._net, self._data, learningrate = self._learning_rate)

    def getDatasetLength(self):
        return len(self._data_source['inp'])

    def activateNetwork(self, value):
        '''@param value must be a sequence of values for input in the network'''
        return self._net.activate(value)

    def __str__(self):
        out =  'PyBrain: '
        for _layer in self._net.modulesSorted:
            out += '< ' + str(self._net.modulesSorted())[1, -1] + ' >\n'
        return out

#NeuroLab----------------------------------------------------------------

class NeuroLabFeedFowardFullConectedNetwork(AbstractFeedFowardNetWork):
    '''
    It is an feedfoward full connected (all nodes from one layer are connected to all other nodes from the next layer) network.
    '''

    def __init__(self, inputSize, topology):
        input_range = [[0., 100.] for i in xrange(inputSize)]
        trans = [_nl.trans.LogSig()]*(len(topology))+[_nl.trans.PureLin()]
        
        topology = list(topology)+[1]
        self._net = _nl.net.newff(input_range, topology, transf=trans)

        self._data = {'input': _np.array([]), 'target': _np.array([])}
        self._learning_rate = 0.01
        self._samples_limit = None
        
        for layer in self._net.layers:
            for i in xrange(len(layer.np['w'])):
                layer.np['w'][i] = 1./ inputSize
            layer.np['b'][:] = 0.
            #del layer.np['b']
        
        self.data_pointer = 0

    def clearDataSet(self):
        self._data['input'] = _np.array([])
        self._data['target'] = _np.array([])

    def addEntriesToDataSet(self, info_array):
        data_size = len(self._data['input'])
        self._data['input'].resize([data_size+len(info_array), len(self._net.inp)], refcheck = False)
        self._data['target'].resize([data_size+len(info_array), len(self._net.out)], refcheck = False)

        for i in xrange(len(info_array)): 
            self._data['input'][data_size + i] += info_array[i][0]
            self._data['target'][data_size + i] += info_array[i][1]
        if self._samples_limit != None:
            extra_space = self.getDatasetLength() - self._samples_limit
            if extra_space > 0:
                self.removeOldestEntriesFromDataSet(extra_space)
#        print "inp size:", len(self._data['input'])
#        raw_input()

    def removeOldestEntriesFromDataSet(self, quantity):
        datasetSize = self.getDatasetLength()
        if datasetSize <= quantity:
            self.clearDataSet()
            return
        self._data['input']  = _np.delete(self._data['input'], xrange(quantity), 0)
        self._data['target'] = _np.delete(self._data['target'], xrange(quantity), 0)


    def removeRandomEntriesFromDataSet(self, quantity):
        datasetSize = self.getDatasetLength()

        if datasetSize <= quantity:
            self.clearDataSet()
            return
        randomList = _random.sample(xrange(datasetSize), quantity)
        self._data['input']  = _np.delete(self._data['input'], randomList, 0)
        self._data['target'] = _np.delete(self._data['target'], randomList, 0)


    def limitDatasetSize(self, value):
        self._samples_limit = value
        if value != None:
            assert value >= 0, 'That value must be positive!'

    def trainNetwork(self, maxEpochs = 100):
        self._net.train(self._data['input'], self._data['target'], show = 0, epochs = maxEpochs, \
                        lr = self._learning_rate, mc=1, lr_inc=0, lr_dec=0)#maxEpochs)# lr = self._learning_rate, goal = 0.05)

    def setLearningRate(self, value):
        self._learning_rate = float(value)
        assert 0 <= self._learning_rate <= 1, 'Learning rate must be between 0 and 1'

    def getDatasetLength(self):
        return len(self._data['input'])

    def activateNetwork(self, value):
        return self._net.sim([value])[0]

    def __str__(self):
        out = 'NeuroLab: '
        for layer in self._net.layers:
            out += '< weights: ' + str(layer.np['w'])+ ' bias: ' + str(layer.np['b'])+' >\n'
        return out
