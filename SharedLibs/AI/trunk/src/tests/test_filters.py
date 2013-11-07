'''
Created on Jan 14, 2013

@author: giulio
'''
from filters import HoltFilter, AdaptableHoltFilter, PerceptronBase, PerceptronFilterPyBrain,\
    PerceptronNeuroLabFilter, SigmoidPerceptron, RollingPerceptron, LazyRollingPerceptron,\
    LazyLinearPerceptron, LinearPerceptron
import random
import unittest


class HoltTests(unittest.TestCase):
    
    def setUp(self):
        self.h = HoltFilter()
        self.testRange = 10
    
    def testInitialization(self):
        """
        Test Holt's initialization routine
        """
        
        self.h.alpha = 1.0
        self.h.beta = 0.0        
        data = 3        
        pred = self.h.apply(data)      
        """
        While not initialized, Holt should output the
        given data
        """
        self.assertAlmostEquals(data, pred)
        
        data += 1
        pred = self.h.apply(data)        
        self.assertAlmostEquals(data, pred)
    
    
    def testLinear(self):
        """
        Test a linear trace
        """
        self.h.alpha = 1.0
        self.h.beta = 0.0
        for i in range(self.testRange):
            pred = self.h.apply(i)
            if i > 1:
                self.assertAlmostEquals(i + 1, pred)


    def testLongForecasting(self):
        """
        Test a linear trace with long forecasting
        """
        self.h.alpha = 1.0
        self.h.beta = 0.0
        self.h.k = 3
        for i in range(self.testRange):            
            pred = self.h.apply(i)
            if i > 1:
                self.assertAlmostEquals(i + self.h.k, pred)

@unittest.skip
class AdaptableHoltTests(HoltTests):
    """
    Adaptable Holt should work just as regular Holt, 
    but with interval based adaptations.
    """

    def setUp(self):
        HoltTests.setUp(self)
        self.h = AdaptableHoltFilter()        
        self.h.windowSize = self.testRange * 2 # must be greater than Holt's original test range


    def testOptimization(self):
        """
        Will use adaptation on a linear trace.
        Expected output should be alpha = 1.0, and beta = 0.0
        """
        for i in range(self.h.windowSize):
            self.h.apply(i)        
        
        self.assertAlmostEquals(self.h.alpha,1.0)
        self.assertAlmostEquals(self.h.beta,0.0)
        
        
    def testAdaption(self):
        """
        Will test the ability to change Holt's parameters at given intervals
        """
        for i in range(self.h.windowSize):
            self.h.apply(random.random() * 2)        
        pars = (self.h.alpha, self.h.beta)
        
        for i in range(self.h.windowSize):
            self.h.apply(i ** 2 + i * 2 + 5 * random.random())            
        new_pars = (self.h.alpha, self.h.beta)
        
        self.assertNotEquals(pars, new_pars)


class TestPerceptronBase(unittest.TestCase):
    PERCEPTRON_CLASS = PerceptronBase
    
    def setUp(self):
        self.learning_rate = 0.01
        self.dataset_size = 5
        self.num_last_measures = 2
        self.lag = 2
        self.perceptron = self.PERCEPTRON_CLASS(self.learning_rate, self.dataset_size, \
                                         self.num_last_measures, self.lag)
    
    def test_creation(self):
        '''
        Creation must happen without errors.
        '''
        self.assertEqual(self.perceptron.learning_rate, self.learning_rate)
        self.assertEqual(self.perceptron.dataset_size, self.dataset_size)
        self.assertEqual(self.perceptron.num_last_measures, self.num_last_measures)
        self.assertEqual(self.perceptron.lag, self.lag)
        self.assertEqual(self.perceptron.data, [])
        self.assertEqual(self.perceptron.last_measures, [])
        self.assertIsInstance(self.perceptron.perceptron, list)
                    
    
    def test_train(self):
        '''
        The train routine must converge after enough training.
        '''
        self.learning_rate = 1e-2
        self.num_last_measures = 1
        self.dataset_size = 10        
        self.perceptron = self.PERCEPTRON_CLASS(self.learning_rate, self.dataset_size, \
                                         self.num_last_measures, self.lag)        
        self.perceptron.data = [([i], i + 1) for i in xrange(self.dataset_size)]
        
        last_error = float('inf')
        target = self.dataset_size
        for i in xrange(100):
            self.perceptron.train()
            error = target - self.perceptron.guess([target - 1])
            self.assertTrue(error <= last_error, msg="Error should go down, but error > last_error")
            last_error = error
    
    def test_apply_buffer_sizes(self):
        '''
        Buffers should be at the expected size.
        '''
        x_list = range(100)
        for x in x_list:
            self.perceptron.apply(x)
            self.assertTrue(len(self.perceptron.data) <= self.perceptron.dataset_size)
            self.assertTrue(len(self.perceptron.last_measures) <= self.perceptron.num_last_measures)
            if hasattr(self.perceptron, 'lag_buffer'):
                self.assertTrue(len(self.perceptron.lag_buffer) <= self.lag)
    
    
@unittest.skip('')
class TestPerceptronFilterPyBrain(TestPerceptronBase):
    PERCEPTRON_CLASS = PerceptronFilterPyBrain
    
    def test_creation(self):
        '''
        Creation must happen without errors.
        '''
        self.assertEqual(self.perceptron.learning_rate, self.learning_rate)
        self.assertEqual(self.perceptron.dataset_size, self.dataset_size)
        self.assertEqual(self.perceptron.num_last_measures, self.num_last_measures)
        self.assertEqual(self.perceptron.lag, self.lag)
        self.assertTrue(self.perceptron.data)
        self.assertEqual(self.perceptron.last_measures, [])
        self.assertTrue(self.perceptron.perceptron)
        

@unittest.skip('')
class TestPerceptronFilterNeuroLab(TestPerceptronBase):
    PERCEPTRON_CLASS = PerceptronNeuroLabFilter
    
    def test_creation(self):
        '''
        Creation must happen without errors.
        '''
        self.assertEqual(self.perceptron.learning_rate, self.learning_rate)
        self.assertEqual(self.perceptron.dataset_size, self.dataset_size)
        self.assertEqual(self.perceptron.num_last_measures, self.num_last_measures)
        self.assertEqual(self.perceptron.lag, self.lag)
        self.assertFalse(self.perceptron.data)
        self.assertEqual(self.perceptron.last_measures, [])
        self.assertTrue(self.perceptron.perceptron)

    
class TestLinearPerceptron(TestPerceptronBase):
    PERCEPTRON_CLASS = LinearPerceptron
    
    def test_creation(self):
        super(TestLinearPerceptron, self).test_creation()
        self.assertEqual(self.perceptron.lag_buffer, [])
        
    def test_apply_correct_data(self):
        '''
        Calling apply must feed the data buffer with correct information.
        '''
        x_list = range(100)
        for x in x_list:
            self.perceptron.apply(x)
            if x >= self.lag + self.num_last_measures - 1:
                expected = (tuple([x - (self.lag - i + 1) for i in xrange(self.lag)]), x + self.lag - self.num_last_measures)
                self.assertTrue(expected in self.perceptron.data, \
                                msg="%s != %s" % (expected, self.perceptron.data))
    
    def test_apply_lag_buffer_full(self):
        '''
        Calling apply until the lag buffer is full.
        '''        
        assert self.lag >= 2
        data = range(self.num_last_measures + self.lag)
        for d in data:
            self.perceptron.apply(d)
        self.assertEqual(self.perceptron.lag_buffer[-1], data[self.num_last_measures + self.lag - 1])
    
    
    def test_apply_data_buffer_full(self):
        '''
        Calling apply until data buffer is full. We also consider the lag and
        num_last_measures.
        '''
        x_list = range(self.dataset_size + self.lag)
        for x in x_list:
            self.perceptron.apply(x)
        
        expected_data = [((a, b), b + self.lag)  for a, b in zip(x_list[:-self.lag], x_list[1:-self.lag])]
        self.assertEqual(self.perceptron.data, expected_data)
        self.assertEqual(self.perceptron.last_measures, x_list[-3:-1])
        

class TestRollingPerceptron(TestPerceptronBase):
    PERCEPTRON_CLASS = RollingPerceptron
    
    def test_apply_correct_data(self):
        '''
        Calling apply must feed the data buffer with correct information.
        '''
        x_list = range(100)
        for x in x_list:
            self.perceptron.apply(x)
            if x > self.lag:
                expected = (tuple([x - (self.num_last_measures - i) for i in xrange(self.lag)]), x)
                self.assertTrue(expected in self.perceptron.data, \
                                msg="%s != %s" % (expected, self.perceptron.data))
    
    def test_apply_intact_last_measures(self):
        '''
        After calling apply, the last_measures buffer must be intact.
        '''
        x_list = range(100)
        for x in x_list:
            self.perceptron.apply(x)
            self.assertEqual(self.perceptron.last_measures[-1], x)
            

class TestLazyRollingPerceptron(TestRollingPerceptron):
    PERCEPTRON_CLASS = LazyRollingPerceptron
    
    def test_laziness(self):
        '''
        Equal data can appear at most once on dataset
        '''
        self.perceptron.dataset_size = 100
        self.perceptron.lag = 1
        x_list = [0, 0, 0, 0, 1, 1, 2, 2]
        for x in x_list:
            self.perceptron.apply(x)
        
        self.assertEqual(self.perceptron.data, [((0, 0), 0), ((0, 0), 1), ((0, 1), 1), ((1, 1), 2), ((1, 2), 2)])
        
        

class TestLazyLinearPerceptron(TestPerceptronBase):
    PERCEPTRON_CLASS = LazyLinearPerceptron
    
    
class TestSigmoidPerceptron(TestLinearPerceptron):
    PERCEPTRON_CLASS = SigmoidPerceptron    
    
if __name__ == "__main__":
    unittest.main()    