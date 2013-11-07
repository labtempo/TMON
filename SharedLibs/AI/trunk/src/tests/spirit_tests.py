'''
Created on Aug 5, 2012

@author: Giulio
'''
import unittest
import spirit, numpy as np


class TestSpirit(unittest.TestCase):
    def setUp(self):
        self.spirit = spirit.Spirit()
        #x_t = spirit.new_matrix(shape=(3, 1))
        #self.spirit.update(x_t)
        
    def assertEqualMatrices(self, m1, m2):
        self.assertEqual(m1.shape, m2.shape)
        for i in range(m1.shape[0]):
            for j in range(m1.shape[1]):
                self.assertAlmostEqual(m1[i, j], m2[i, j], places=3)    
    
    def testInitialization(self):
        # matrix shapes
        self.assertEquals(self.spirit.d.shape, (self.spirit.n, 1))
        self.assertEquals(self.spirit.w.shape, (self.spirit.n, self.spirit.n))
                
        # d initialization
        for i in range(self.spirit.d.shape[0]):
            self.assertEqual(self.spirit.d[i], spirit.SMALL_POSITIVE_VALUE)
        
        # w initialization
        for i in range(self.spirit.w.shape[1]):            
            for j in range(self.spirit.w.shape[0]):                
                if i == j:
                    self.assertEqual(self.spirit.w[j, i], 1.0)
                else:
                    self.assertEqual(self.spirit.w[j, i], 0.0)
                   
    
    def testTrackW(self):
        self.spirit = spirit.Spirit(k=1)
        x_t = spirit.new_matrix(shape=(self.spirit.n, 1))        
        for i in range(self.spirit.n): # [1, 2, 3]^T
            x_t[i] = i + 1       
        
        prev_w_shape = self.spirit.w[0].shape
        prev_w_len = len(self.spirit.w)
        self.spirit._trackW(x_t, self.spirit.k, self.spirit.w, self.spirit.d, self.spirit.l)        
                
        oracle_d = np.mat([ self.spirit.l * spirit.SMALL_POSITIVE_VALUE +  1 * 1 + 0 * 2 + 0 * 3 ])
        self.assertEqual(self.spirit.d[0], oracle_d[0])
        
        self.assertEqual(prev_w_shape, self.spirit.w[0].shape)
        self.assertEqual(prev_w_len, len(self.spirit.w))
        
        # test normality
        self.assertEqual(np.linalg.norm(self.spirit.w[:,:self.spirit.k]), 1)
        

    def testAnomalyDetection(self):
        n = 3
        x_t = spirit.new_matrix(shape=(n, 1))
        for i in range(n): # [1, 2, 3]^T
            x_t[i] = i + 1
        k, w, y = self.spirit.update(x_t)
        x_tilde = self.spirit.reconstruct(w, k, y)
        self.assertEqualMatrices(x_tilde, x_t)
        

class TestMain(unittest.TestCase):
    def testValidArguments(self):
        # default
        spirit.main("spirit col2arff_test.arff".split())
        # with optional parameters 
        spirit.main("spirit col2arff_test.arff -et 0.95 0.97 -of -23 -l 0.78 -k 1".split())
        
    def testInvalidArguments(self):
        # not enough arguments
        self.assertRaises(SystemExit, spirit.main, "spirit".split())        
        # invalid file
        self.assertRaises(SystemExit, spirit.main, "spirit invalidFile.txt".split())

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()