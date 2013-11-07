from SharedLibs.tracetools import TraceReader
from lmfit import minimize, Parameters
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
import collections
import neurolab as nl
import nnetworks as nn
import numpy as np
import pybrain

'''
Decorators
'''
def hard_learning_decorator(perceptron_class):
    class HardLearningPerceptron(perceptron_class):
        '''
        This class will keep the most hard to learn instances on the dataset.
        '''
        def __init__(self, *args, **kwargs):
            super(HardLearningPerceptron, self).__init__(*args, **kwargs)            
            self.error_threshold = .3
        
        def train(self):
            super(HardLearningPerceptron, self).train()
            if self.dataset_size > 1:
                errors = [abs(y - self.guess(x)) for x, y in self.data]
                avg_error = sum(errors) / self.dataset_size
                new_dataset = []
                for i in xrange(len(self.data)):
                    if errors[i] > avg_error * self.error_threshold:
                        new_dataset.append(self.data[i])
                self.data = new_dataset
            
            self.dataset_size = len(self.data) + 1
            
    return HardLearningPerceptron


def rolling_decorator(perceptron_class):
    class RollingPerceptron(perceptron_class):
        '''
        Perceptron that predicts the next step in a rolling fashion.
        '''
        def __init__(self, *args, **kwargs):
            perceptron_class.__init__(self, *args, **kwargs)
                    
        def apply(self, x):
            if len(self.last_measures) < self.num_last_measures:
                self.last_measures.append(x)                            
                return x
            
            self.data.append((tuple(self.last_measures), x))
                            
            self.train()
            
            if len(self.data) == self.dataset_size:
                del self.data[0]
                                    
            last_measures = self.last_measures[:]        
            prediction = x
            for _i in xrange(self.lag):            
                prediction = self.guess(last_measures)
                del last_measures[0]
                last_measures.append(prediction)
            
            del self.last_measures[0]
            self.last_measures.append(x)
            
            return prediction
    return RollingPerceptron


def lazy_trainer_decorator(perceptron_class):
    class LazyTrainerPerceptron(perceptron_class):
        def train(self):
            # look for a tuple that matches the current
            d = self.data.pop()
            
            if not d in self.data:            
                self.data.append(d) 
                perceptron_class.train(self)
            else:
                self.data.append(d)
    return LazyTrainerPerceptron


def lazy_decorator(perceptron_class):
    class LazyPerceptron(perceptron_class):
        def train(self):
            # look for a tuple that matches the current
            d = self.data.pop()
            
            if not d in self.data:            
                self.data.append(d) 
                perceptron_class.train(self)            
    return LazyPerceptron


def select_different_decorator(perceptron_class):
    class DiffDecorator(perceptron_class):
        def train(self):
            # look for a tuple that matches the current
            if self.num_last_measures == 1:
                perceptron_class.train(self)
                return
            
            d = self.data.pop()
            
            x = d[0]
            element = x[0]
            diff = False
            for i in xrange(1, self.num_last_measures):
                if x[i] != element:
                    diff = True
                    break
            
            if diff:     
                self.data.append(d)
                
            perceptron_class.train(self)
    return DiffDecorator


def finite_diffs_decorator(perceptron_class):
    class FiniteDiffPerceptron(perceptron_class):
        def train(self):
            last_data = self.data[-1]
            x = last_data[0]
            x = [(x[-1] - x[i]) / (i + 1) for i in xrange(self.num_last_measures - 1)] + [x[-1]]            
            
            self.data[-1] = (x, self.data[-1][1])
            #print self.data
                        
            perceptron_class.train(self)
            
            
    return FiniteDiffPerceptron

'''
Filters
'''

class Filter(object):
    def __init__(self):
        self.training_delay = 0
    
    def apply(self, x):
        raise NotImplementedError, "Must provide .apply()"
    
    
class DummyFilter(Filter):
    def apply(self, x):
        return x
    
    def __repr__(self):
        return "<DummyFilter>"
    
Naive = Reactive = DummyFilter


class MultivariateFilter(Filter):
    def __init__(self, filter_cls, filter_kwargs, series_count):
        self.filters = [filter_cls(**filter_kwargs) for _i in xrange(series_count)]        
        self.training_delay = max(f.training_delay for f in self.filters)
        
    def apply(self, x):
        result = [self.filters[i].apply(x[i]) for i in xrange(len(x))]
        return result
    
    def __repr__(self):
        return "%s (multivariate)" % (self.filters[0].__repr__())

class MovingAverage(Filter):
    def __init__(self, size):
        self.size = size
        self.training_delay = size
        self.summation = 0
        self.buffer = []
    
    def apply(self, x):
        self.summation += x
        self.buffer.append(x)
        if len(self.buffer) > self.size:             
            self.summation -= self.buffer[0]
            del self.buffer[0]                
        
        return self.summation / len(self.buffer)


class Oracle(Filter):
    def __init__(self, trace_path, lag):        
        oracle_trace = TraceReader(trace_path)
        
        self.trace_gen = oracle_trace.read()
        for _i in xrange(lag - 1):
            self.trace_gen.next()
        self.training_delay = 0
        self.last_value = 0
            
    def apply(self, x):
        if self.trace_gen:
            try:
                self.last_value = self.trace_gen.next()
            except StopIteration:
                self.trace_gen = None
        
        return self.last_value        


class PerceptronBase(Filter):
    def __init__(self, learning_rate=0.0001, dataset_size=100, num_last_measures=1, lag=1):
        '''
        @param num_last_measures: training vector norm
        @param lag: lead prediction interval
        '''
        self.learning_rate = learning_rate
        self.dataset_size = dataset_size        
        self.num_last_measures = num_last_measures
        self.last_measures = []
        self.lag = lag
        self.training_delay = 0
        self.data = []
        
        # perceptron weights
        self.perceptron = [1. / self.num_last_measures for _i in xrange(self.num_last_measures)]
    
    def train(self):
        pass
    
    def guess(self, x):
        return x[-1]
    
    def apply(self, x):
        self.data.append(x)
        if len(self.data) > self.dataset_size:
            del self.data[0]
            
        return self.guess([x])
    
    def debug(self):
        return ", ".join("%1.6f" % p for p in self.perceptron)
    
    def __repr__(self):
        return "<%s>" % (self.__class__.__name__,)
       
        
class LinearPerceptron(PerceptronBase):
    def __init__(self, *args, **kwargs):       
        super(LinearPerceptron, self).__init__(*args, **kwargs)
                        
        # used to make predictions
        self.lag_buffer = []    
    
    def delta(self, y):
        return 1
    
    
    def train(self):
        for x, y in self.data:
            error = y - self.guess(x)
            for i in xrange(self.num_last_measures):
                self.perceptron[i] += self.learning_rate * error * self.delta(y) * x[i]
                        
    def guess(self, x):   
        #perceptron_out = np.dot(x, self.perceptron)
        perceptron_out = sum(x[i] * self.perceptron[i] for i in xrange(len(x)))     
        return perceptron_out


    def apply(self, x):
        if len(self.lag_buffer) < max(self.lag - 1, 1):
            if len(self.last_measures) < self.num_last_measures:
                self.last_measures.append(x)
            else:
                self.lag_buffer.append(x)                  
            return x
        
        self.lag_buffer.append(x)
        self.data.append((tuple(self.last_measures), self.lag_buffer[-1]))
                                
        self.train()
        
        if len(self.data) == self.dataset_size:        
            del self.data[0]
            
        del self.last_measures[0]
        self.last_measures.append(self.lag_buffer[0])
        
        del self.lag_buffer[0]
                        
        return self.guess(self.last_measures)


class MultiLayerPerceptron(PerceptronBase):
    def __init__(self, learning_rate=0.0001, dataset_size=100, num_last_measures=1, lag=1, topology = None, \
                 networkBuilder = nn.NeuroLabFeedFowardFullConectedNetwork, maxEpochs=1): \
                 #networkBuilder = nn.PyBrainFeedFowardFullConectedNetwork, maxEpochs=1):
        '''
        @param num_last_measures: training vector cardinality
        @param lag: lead prediction interval
        '''
        assert issubclass(networkBuilder, nn.AbstractFeedFowardNetWork)
        if not topology:
            topology = []
        self.net = networkBuilder(num_last_measures, list(topology))
        self.net.limitDatasetSize(dataset_size)
        self.net.setLearningRate(learning_rate) 
        self.num_last_measures = num_last_measures
        self.last_measures = []
        self.lag_buffer = []
        self.maxEpochs = maxEpochs
        self.dataset_size = dataset_size
        self.lag = lag
        self.training_delay = 0 #??
        self.data = []
    
    def train(self):
        self.net.trainNetwork(maxEpochs = self.maxEpochs)
    
    def guess(self, x):
        y = self.net.activateNetwork(x)[0]
        #y = float(y * (self.max_val - self.min_val) + self.min_val)
        return y
    
    def apply(self, x):
        #creating fake lead
        if len(self.lag_buffer) < max(self.lag - 1, 1):
            if len(self.last_measures) < self.num_last_measures:
                self.last_measures.append(x)
            else:
                self.lag_buffer.append(x)                  
            return x
        
        self.lag_buffer.append(x)
        self.net.addEntriesToDataSet([[ self.last_measures, [self.lag_buffer[-1]] ]])
        #Preparing network to well adapt to new data 
        if self.net.getDatasetLength() < self.dataset_size:
            return x
        self.train()
        
        del self.last_measures[0]
        self.last_measures.append(self.lag_buffer[0])
        del self.lag_buffer[0]
        y = self.guess(self.last_measures)
        return y
    
    def debug(self):
        return self.net

RollingPerceptron = rolling_decorator(LinearPerceptron)
LazyLinearPerceptron = lazy_decorator(LinearPerceptron)
LazyRollingPerceptron = lazy_decorator(RollingPerceptron)
FiniteDiffPerceptron = finite_diffs_decorator(LinearPerceptron)
DiffPerceptron = select_different_decorator(LinearPerceptron)
HardLearningLinearPerceptron = hard_learning_decorator(LinearPerceptron)


class PerceptronNeuroLabFilter(LinearPerceptron):
    def __init__(self, *args, **kwargs):    
        super(PerceptronNeuroLabFilter, self).__init__(*args, **kwargs)                        
        self.lag_buffer = collections.deque(maxlen=self.lag)
        
        #self.iarray = np.array([[1.] * self.num_last_measures for _ in xrange(self.dataset_size)])
        #self.tarray = np.array([[1.] for _ in xrange(self.dataset_size)])
        #self.dataPos = 0

        #imput neurons weights, output neuron weights, (quantity of input neurons, quantity of output neurons)
        #self.perceptron = nl.net.newff([[0.5 for i in range(self.num_last_measures)], [0.5 for i in range(self.num_last_measures)]], [1,1])
        self.perceptron = nl.net.newp([[0, 1]] * self.num_last_measures, 1)
        for layer in self.perceptron.layers:
            layer.np['w'][:] = 1. / self.num_last_measures
        #print "perceptron:", [self.perceptron.layers[i].np['w'] for i in xrange(len(self.perceptron.layers))]

    def train(self):
        #nl.train.train_gd(self.perceptron, self.iarray, target=self.tarray, epochs=1, #@UndefinedVariable \
        #                  lr=self.learning_rate, show=0)
        iarray = [[[d] for d in data[0]] for data in self.data]
        tarray = [[data[1]] for data in self.data]        
        self.perceptron.train(iarray, tarray, show=0, epochs=1, lr=self.learning_rate)
    
    def guess(self, x):
        y = self.perceptron.sim(np.array(self.last_measures))
        y = float(y * (self.max_val - self.min_val) + self.min_val)
        return y
    
    
class PerceptronPyBrainFilter(LinearPerceptron): # PYBRAIN
    def __init__(self, *args, **kwargs):    
        super(PerceptronPyBrainFilter, self).__init__(*args, **kwargs)
        
        # input, hidden_layers, output
        self.perceptron = buildNetwork(self.num_last_measures, 0, 1, \
                                       hiddenclass=pybrain.structure.modules.SigmoidLayer, #@UndefinedVariable \
                                       outclass=pybrain.structure.modules.SigmoidLayer) #@UndefinedVariable
        
        # input dimension, target dimension
        self.pointer = 0
        self.data = SupervisedDataSet(self.num_last_measures, 1)
        for _i in xrange(self.dataset_size):
            self.data.addSample([0] * self.num_last_measures, 0)     
        self.trainer = BackpropTrainer(self.perceptron, self.data, learningrate=self.learning_rate)
        
        # This call does some internal initialization which is necessary before the net can finally
        # be used: for example, the modules are sorted topologically.
        self.perceptron.sortModules()
        

    def train(self):
        self.trainer.trainEpochs(1)
    
    
    def guess(self, x):
        return self.perceptron.activate(x)
    

    def apply(self, x):                
        if len(self.lag_buffer) < self.lag - 1:
            if len(self.last_measures) < self.num_last_measures:
                self.last_measures.append(x)
            else:
                self.lag_buffer.append(x)                  
            return x
        
        self.lag_buffer.append(x)
        #self.data.addSample(tuple(self.last_measures), self.lag_buffer[-1])
        self.data['input'][self.pointer] = np.array(self.last_measures)
                                                
        self.train()
        
        if len(self.data) == self.dataset_size:        
            #del self.data[0]
            #self.data.removeSample
            #self.data.removeSample
            pass
            
        del self.last_measures[0]
        self.last_measures.append(self.lag_buffer[0])
        
        del self.lag_buffer[0]
                        
        return self.guess(self.last_measures)


class SigmoidPerceptron(LinearPerceptron):
    def __init__(self, *args, **kwargs):
        super(SigmoidPerceptron, self).__init__(*args, **kwargs)        
        self.max_val = -float('inf')
        self.min_val = float('inf')
        self.range = 0
        
    def delta(self, y):
        #return y * (1. - y)
        derivative = 1. / (1. + np.exp(-y))
        return derivative * (1. - derivative)
                        
    def guess(self, x):
        z = super(SigmoidPerceptron, self).guess(x)
        z = 1. / (1. + np.exp(-z))  
        return z
    
    def apply(self, x):
        if x > self.max_val: 
            self.max_val = x
            self.range = self.max_val - self.min_val
        if x < self.min_val:
            self.min_val = x
            self.range = self.max_val - self.min_val
                
        y = super(SigmoidPerceptron, self).apply(x)
                
        return y * self.range + self.min_val
    
    def __repr__(self):
        return "<SigmoidPerceptron>"
    
    
class ExpFilter(Filter):
    def __init__(self, alpha=0.5):
        super(ExpFilter, self).__init__()
        self.training_delay = 1
        self.alpha = alpha        
        self.S = 0.0
        self.initialized = False
    
    def _initialized_apply(self, x):
        self.S = self.alpha * x + (1 - self.alpha) * self.S 
        return self.S
    
    def apply(self, x):
        if not self.initialized:
            self.S = x
            self.initialized = True
        self.S = self.alpha * x + (1 - self.alpha) * self.S 
        return self.S
    
    def __repr__(self):
        return "<ExpFilter: alpha=%f>" % self.alpha

ExpAvg = ExpFilter


class BootstrapingExpFilter(ExpFilter):
    def __init__(self, alpha=0.5, k=1):
        super(BootstrapingExpFilter, self).__init__()
        self.k = k
    
    def apply(self, x):
        self.S = ExpFilter.apply(self, x)
        old_S = self.S
        for _i in xrange(self.k - 1):
            self.S = ExpFilter.apply(self, x)
        result = self.S
        self.S = old_S
        return result
    
    def __repr__(self):
        return "<Bootstraping ExpFilter: alpha=%f, k=%d>" % (self.alpha, self.k)


class ExpFilterARRSES(Filter):
    '''
    Adaptive Exponential Filter.
    @attention: not tested.
    '''
    def __init__(self, alpha=0.5):
        ExpFilter.__init__(self, alpha)
        self.A = 0.0
        self.M = 0.0
        self.F = 0.0
        self.alpha = 0.5
        self.beta = 0.0

    def apply(self, x):        
        self.F = self.alpha * x + (1.0 - self.alpha) * self.F
        
        E = x - self.F
        self.A = self.beta * E + (1.0 - self.beta) * self.A
        self.M = self.beta * abs(E) + (1.0 - self.beta) * self.M
        
        self.alpha = abs(self.A / self.M)
        
        return self.F


class HoltFilter(Filter):
    def __init__(self, alpha=0.5, beta=0.5, k=1):
        super(HoltFilter, self).__init__()
        self.training_delay = 2
        self.alpha = alpha
        self.beta = beta  
        self.k = k
        self._initialized = 0
        self.S = 0.0
        self.B = 0.0


    def apply(self, x):        
        if self._initialized <= 1:
            if self._initialized == 0:
                self.S = x
                self.B = x
            else: #self._initialized == 1:
                self.B = x - self.B
            self._initialized += 1
            return x            
                     
        old_S = self.S
        self.S = self.alpha * x + (1. - self.alpha) * (self.S + self.B)
        self.B = self.beta * (self.S - old_S) + (1. - self.beta) * self.B
        
        return self.S + self.B * self.k
    
    def __repr__(self):
        return "<HoltFilter: alpha=%f, beta=%f, k=%d>" % (self.alpha, self.beta, self.k)


class BehavedHolt(HoltFilter):
    def __init__(self, alpha=0.5, beta=0.5, k=1):
        super(BehavedHolt, self).__init__(alpha=alpha, beta=beta, k=k)
        self.max_inc = 5.0
    
    def apply(self, x):
        if self._initialized <= 1:
            if self._initialized == 0:
                self.S = x
                self.B = x
            else: #self._initialized == 1:
                self.B = x - self.B
            self._initialized += 1
            return x            
                     
        old_S = self.S
        self.S = self.alpha * x + (1. - self.alpha) * (self.S + self.B)
        self.B = self.beta * (self.S - old_S) + (1. - self.beta) * self.B
        
        sign_B = 1 if self.B >= 0 else -1
        self.B = min(abs(self.B), self.max_inc / self.k) * sign_B
        
        return self.S + self.B * self.k
    

MSE = 0
MAE = 1
MAPE = 2
HIB = 3

ERROR_TO_STR = {MSE: "MSE", MAE: "MAE", MAPE: "MAPE", HIB: "HIB"}

def error(x1, x2, method=MSE):
    if method == MSE:
        return (x1 - x2) ** 2
    elif method == MAE:
        return abs(x1 - x2)
    elif method == HIB:
        if x2 > x1:
            return (x1 - x2) ** 2
        else:
            return abs(x1 - x2)
    elif method == MAPE:                                
        if x2 > 0:
            return abs((x1 - x2)/x2)


class AdaptableHoltFilter(BehavedHolt):
    def __init__(self, lag, window_size=10, minimize_kws=None, use_grid=False):
        self.DEFAULT_ALPHA = 0.5
        self.DEFAULT_BETA = 0.01
                        
        BehavedHolt.__init__(self, alpha=self.DEFAULT_ALPHA, beta=self.DEFAULT_BETA, k=lag)        
        self.data = []
        self.window_size = window_size
        self.lag = lag
        self.training_delay = window_size + lag
        self.params = Parameters()
        self.params.add('alpha', value=self.DEFAULT_ALPHA, min=0.01, max=1.0)
        self.params.add('beta',  value=self.DEFAULT_BETA,  min=0.01, max=1.0)
        self.lmfit_calls = 0
        self.lmfit_fails = 0
        self.minimize_kws = {'maxfev': 1000} if not minimize_kws else minimize_kws
        self.use_grid = use_grid
        self.starting_pars = (self.S, self.B)
                
        def calc_residuals(params, lag, data):
            errors = []
            alpha = params['alpha'].value
            beta = params['beta'].value                                   
            S = self.starting_pars[0]
            B = self.starting_pars[1]
            old_S = S
            
            for i in xrange(len(data) - lag):                
                old_S = S         
                S = alpha * data[i] + (1. - alpha) * (S + B)
                B = beta * (S - old_S) + (1. - beta) * B
                y = S + B * self.k
                     
                errors.append(y - data[i + lag])
                
            return errors
        
        self.calc_residuals = calc_residuals
        
    def grid_optimize_pars(self, precision=0.1):    
        def calc_error(alpha, beta):
            holt = BehavedHolt(alpha=alpha, beta=beta, k=self.k)
            SE = 0.0
            for i in range(len(self.data) - self.lag):
                prediction = holt.apply(self.data[i])                
                SE += (prediction - self.data[i + self.lag]) ** 2
            return SE
            
        smaller_se = calc_error(self.alpha, self.beta)
        result = (self.alpha, self.beta)
        
        alpha = 1.0
        while alpha >= 0.0:
            beta = 1.0
            while beta >= 0.0:
                SE = calc_error(alpha, beta)                    
                
                if SE < smaller_se:
                    result = (alpha, beta)
                    smaller_se = SE
                
                beta -= precision              
            alpha -= precision
             
        return result
    
    
    def optimize_pars(self):
        #self.params['alpha'].value = self.alpha
        #self.params['beta'].value = self.beta
        
        ret = minimize(self.calc_residuals, self.params, args=(self.lag, self.data), **self.minimize_kws)
        if ret.ier > 1:
            if self.use_grid:
                return self.grid_optimize_pars()            
            return None
        
        return (self.params['alpha'].value, self.params['beta'].value)
    
    
    def apply(self, x):
        self.data.append(x)
        
        best_pars = None
        if len(self.data) == self.window_size + self.lag:
            best_pars = self.optimize_pars()
            if best_pars:
                self.alpha, self.beta = best_pars
                print self   
            else:
                self.lmfit_fails += 1
            self.lmfit_calls += 1
            
            del self.data[:self.window_size]
            self.starting_pars = (self.S, self.B)
        
        ret = BehavedHolt.apply(self, x)                
        return ret


class KalmanFilter(Filter):
    '''
    Code based on: http://www.scipy.org/Cookbook/KalmanFiltering
    '''
    
    def __init__(self, *args, **kwds):
        super(KalmanFilter, self).__init__()        
        self.Pminus = 0.0
        self.xhat = 0.0
        self.xhatminus = 0.0
        self.K = None
        self.P = 1.0
        self.Q = 1e-5 #process noise covariance
        self.R = 0.1**2 #measurement noise covariance
        self.pred = HoltFilter(alpha=0.9,beta=0.4)
        self.alpha = 0.8

    def apply(self, z):
        # time update
        self.xhatminus = self.xhat
        #self.xhatminus = self.pred.apply(self.xhat)
        self.Pminus = self.P + self.Q
    
        # measurement update
        self.K = self.Pminus /(self.Pminus + self.R)
        #self.xhat = self.xhatminus + self.K * (z - self.xhatminus)
        self.xhat = self.xhatminus + self.K * (z - self.xhatminus)
        if self.xhat < 0: self.xhat = 0
        self.P = (1.0 - self.K) * self.Pminus
        return self.xhatminus
          
    
    def __repr__(self):
        return 'K = %f, P = %f' % (self.K,self.P)


class ARFilter(Filter):
    def __init__(self, phi, order):        
        assert order >= 1, 'Invalid order number specified'
                
        self.order = order            
        self._model = np.array(phi)
        self._data = []
        self._last_measures = [1.0]
        self.training_delay = order
        
        
    def guess(self, X):
        """
        @param X must have cardinality equals to the ar method order
        @param model must be a dictionary where 'c' is an constant float and 'phi' is a list of floats
        
        @note: X holds the last measurements where the most recent ones are appended to the right
        @note: the order of phi is: lag n, lag n-1, ..., lag 2, lag 1
        """
        return float(np.dot(X, self._model))
    
    
    def apply(self, x):
        self._last_measures.insert(1, x)
        
        if len(self._last_measures) < self.order + 1:
            return x
        
        if len(self._last_measures) > self.order + 1:
            del self._last_measures[-1]
                                        
        return self.guess(self._last_measures)



class AdaptableARFilter(ARFilter):
    def __init__(self, lag, dataset_size=50, minimize_kws=None):             
        self.DEFAULT_PHI = [0.01, 0.9, 0.1]
        ARFilter.__init__(self, self.DEFAULT_PHI, 2)
                        
        self.lag = lag           
        self.dataset_size = dataset_size
        self._data = []
        self.training_delay = dataset_size + self.order        
        self._initialized = False
        self.lmfit_fails = 0
        self.lmfit_calls = 0
        self.minimize_kws = {'maxfev': 1000} if not minimize_kws else minimize_kws
        
        self.cached_guess = 0.0
        self.dirty_cache = True
        self.params = Parameters()
        self.params.add('c',    value=self.DEFAULT_PHI[0], min=-10.0, max=10.0)
        #self.params.add('phi1', value=self.DEFAULT_PHI[1])
        #self.params.add('phi2', value=self.DEFAULT_PHI[2])
                
        self.params.add('phi_sum', min=-1, max=1, value=self.DEFAULT_PHI[2] + self.DEFAULT_PHI[1], vary=True)
        self.params.add('phi_diff', min=-1, max=1, value=self.DEFAULT_PHI[2] - self.DEFAULT_PHI[1], vary=True)
        self.params.add('phi1', expr='(phi_sum - phi_diff)/2.0')
        self.params.add('phi2', expr='(phi_sum + phi_diff)/2.0')        
                        
        def calc_residuals(params, lag, data):
            errors = []
                        
            phi = [params['c'].value, params['phi1'].value, params['phi2'].value]                        
                                    
            forecaster = ARFilter(phi, self.order)
            
            # initialize
            for i in xrange(self.order - 1):
                forecaster.apply(data[i])
            
            for i in xrange(self.order - 1, len(data) - 1):
                y = forecaster.apply(data[i])
                errors.append(y - data[i + 1])
                            
            return errors
        
        self.calc_residuals = calc_residuals
        
    
    def __repr__(self):
        return "<AR(%d): %s>" % (self.order, self._model)
    
    
    def optimize_parameters(self, data):        
        #self.params['c'].value = self._model[0]
        #self.params['phi_sum'].value = self._model[2] + self._model[1]
        #self.params['phi_diff'].value = self._model[2] - self._model[1]
                        
        '''
        epsfcn : float
        A suitable step length for the forward-difference approximation of the Jacobian (for Dfun=None). 
        If epsfcn is less than the machine precision, it is assumed that the relative errors in the functions are of 
        the order of the machine precision.
        '''
        ret = minimize(self.calc_residuals, self.params, args=(self.lag, self._data), **self.minimize_kws)
        
        if ret.ier > 1:
            return False
                        
        self._model = [self.params['c'].value, self.params['phi1'].value, self.params['phi2'].value]
        
        return True
        
    def guess(self, X):
        _X = X[:]
        y = 0.0
        for _i in xrange(self.lag):
            y = ARFilter.guess(self, _X)
            _X.insert(1, y)
            del _X[-1]
        return y
    
    
    def apply(self, x):
        self._last_measures.insert(1, x)
        self._data.append(x)
        
        if len(self._last_measures) < self.order + 1:
            return x
        
        self.dirty_cache = any(self._last_measures[i] != self._last_measures[i + 1] for i in xrange(1, len(self._last_measures) - 1))
        
        if len(self._last_measures) > self.order + 1:
            del self._last_measures[-1]
                            
        if len(self._data) - self.order < self.dataset_size and not self._initialized:
            return x
        
        if len(self._data) - self.order == self.dataset_size:
            self._initialized = True                 
            if not self.optimize_parameters(self._data):
                self.lmfit_fails += 1
                #print 'failed'
            else:
                print self._model
                self.dirty_cache = True
            self.lmfit_calls += 1
            del self._data[:self.dataset_size]
        
        if not self.dirty_cache:
            ret = self.cached_guess
        else:
            ret = self.guess(self._last_measures)
            self.cached_guess = ret
                 
        return ret


class Bote(Filter):
    def __init__(self):
        super(Bote, self).__init__()
        self.S = None

    def apply(self, x):
        if self.S is None:
            self.S = x
            return x
        
        result = 2 * x - self.S
        self.S = x
        return result


class SmoothingBote(Bote):
    def __init__(self, alpha):
        Bote.__init__(self)
        self.alpha = alpha
    
    def apply(self, x):
        if self.S is None:
            self.S = x
            return x
        
        result =  (1. - self.alpha) * x - self.alpha * (x - self.S)
        self.S = x
        return result
        

if __name__ == '__main__':
    import timeit

    def runFilter(filterName, filterClass, iterations, data, args=[], kwargs={}):
        print filterName, 'Benchmark'
        method = """
    import random
    from __main__ import %s, error
    
    step = 20   
    data = %s
    result = float('inf')
    filter = %s(*%s, **%s)
    SE = 0.0

    for i in xrange(len(data) - 1):
        prediction = filter.apply(data[i])                
        SE += error(prediction, data[i+1])                       
        if SE > result:
            break
    if SE < result:
        result = SE
    print "SE:", result
    """ %(filterClass.__name__, repr(data), filterClass.__name__, args, kwargs)
        t = timeit.Timer(stmt=method)
        return t.timeit(number=iterations)/iterations

    
    data = [i for i in xrange(2400)]
    unitConversor = 1e+6
    unit = "usec/pass"
    iterations = 1
    print ("method 1: %.2f " + unit) % (unitConversor * runFilter('AR-Breno', ARFilter, iterations, data, \
                                                                  args=(1, ), kwargs={"dataset_size": 2}))
    '''
    print ("method 2: %.2f " + unit) % (unitConversor * runFilter('MultiLayerPerceptron-Breno Online',\
                                                                  MultiLayerPerceptron, iterations, data))
    print ("method 3: %.2f " + unit) % (unitConversor * runFilter('Perceptron-Breno Online',\
                                                                  LinearPerceptron, iterations, data))
    print ("method 4: %.2f " + unit) % (unitConversor * runFilter('SigmoidPerceptron-Breno Online',\
                                                                  SigmoidPerceptron, iterations, data))
    print ("method 5: %.2f " + unit) % (unitConversor * runFilter('Perceptron[NeuroLab] Online',\
                                                                  PerceptronNeuroLabFilter, iterations, data))
    print ("method 6: %.2f " + unit) % (unitConversor * runFilter('Perceptron[PyBrain] Online',\
                                                                  PerceptronPyBrainFilter, iterations, data))
    '''