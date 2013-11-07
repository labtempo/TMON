'''
Created on Sep 30, 2012

@author: Giulio
'''
import unittest
import mkchain
import numpy as np


class TestMarkovChain(unittest.TestCase):
    def setUp(self):
        self.mkchain = mkchain.MarkovChain(10, 2)
            
    def testSmoke(self):
        pass
    
    def testUpdate(self):
        data = np.random.normal(size=20)
        for d in data:
            self.mkchain.update(abs(d / 2.))
        self.assertEqual(len(self.mkchain.data_buffer), self.mkchain.window_len)
        
    def testCalcProbs(self):
        self.mkchain.transition_matrix[0,0] = 2
        self.mkchain.transition_matrix[0,1] = 8
        self.mkchain.transition_matrix[1,0] = 5
        self.mkchain.transition_matrix[1,1] = 5
        probs = self.mkchain.calc_state_probs()


class TestRangeMC(TestMarkovChain):
    def setUp(self):
        self.mkchain = mkchain.RangeMarkovChain(10, 2)


class TestReadingFreq(unittest.TestCase):
    def setUp(self):
        self.readingFreq = mkchain.ReadingFreq(max_readings=10)
            
    def testSmoke(self):
        pass
    
    def testPercentile(self):
        max_range = self.readingFreq.max_readings * 2
        for i in xrange(max_range):
            self.readingFreq.update(i)
        
        # 100%
        p = self.readingFreq.percentile(100)
        self.assertEqual(p, max_range - 1)
    
        # 50%
        p = self.readingFreq.percentile(50)
        self.assertEqual(p, (max_range - 10) * .5)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSmoke']
    unittest.main()