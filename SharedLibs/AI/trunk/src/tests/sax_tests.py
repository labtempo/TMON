import unittest
import numpy as np
import random

from sax import SAX
from ts_bitmaps import TimeseriesBitmap

__author__ = "Aleksandar Mastilovic"
__copyright__ = "Copyright 2012, Aleksandar Mastilovic"
__credits__ = ["Aleksandar Mastilovic"]
__version__ = "1.0.1"
__maintainer__ = "Aleksandar Mastilovic"
__email__ = "aleksandar.mastilovic@gmail.com"
__status__ = "Development"


class testSax(unittest.TestCase):
    def setUp(self):
        self.sax = SAX()
        self.delta = 1.0e-10

    def testEuclideanDistance(self):
        sig1 = [ i for i in xrange(100) ]
        sig2 = [ i + 0.5 for i in xrange(100) ]
        lse = self.sax.euclidean_dist(sig1, sig2)
        assert lse == 5.0

    def testNormalizeOnRandom(self):
        orig_sig = [ random.uniform(0, 1) for _ in xrange(1000) ]
        sig = self.sax.normalize(orig_sig)

        # properly Z-normalized signal should have a mean
        # very close to 0 and standard deviation very close to 1.0
        assert abs(np.mean(sig)) < self.delta
        assert abs(np.std(sig) - 1.0) < self.delta

    def testPAA(self):
        siglen = 100
        M = 10
        orig_sig = [ random.uniform(0, 1) for _ in xrange(siglen) ]
        paa_sig = self.sax.to_PAA(orig_sig, M)

        self.assertEquals(len(paa_sig), M)
        self.assertEquals(np.mean(orig_sig[:M]), paa_sig[0])

    def testPAAexample(self):
        orig_sig = [2.02, 2.33, 2.99, 6.85, 9.20, 8.80, 7.50, 6.00, 5.85, 3.85, 4.85, 3.85, 2.22, 1.45, 1.34]
        M = 9
        paa_sig = self.sax.to_PAA(orig_sig, M)
        res_sig = [-0.9327168, -0.3699053, 1.383673, 1.391248, 0.6299752, 0.01641218, -0.05933634, -0.8387886, -1.220561]

        assert len(paa_sig) == len(res_sig)

        M = 5
        paa_sig = self.sax.to_PAA(orig_sig, M)
        res_sig2 = [-0.9379922, -0.0857173, 0.4738943, 1.444949, -0.8951336]

        assert len(paa_sig) == len(res_sig2)
    
    def testPAAZero(self):
        orig_sig = [0] * 20
        paa_sig = self.sax.to_PAA(orig_sig, 5)        
        self.assertTrue(not any(paa_sig))
        self.assertEqual(self.sax.convert(orig_sig, "abcd"), "aaaaaaaa")

class testBitmap(unittest.TestCase):
    def setUp(self):
        size = 2
        self.alphabet = "abcd"
        self.bitmap = TimeseriesBitmap(self.alphabet, size)
    
    def testAnomalyScore(self):
        # put some data on the bitmap
        self.bitmap.frequencies["aa"] = 3
        self.bitmap.frequencies["ab"] = 4        
        score = self.bitmap.getAnomalyScore(self.bitmap)                
        self.assertEqual(score, 0)
                
        self.bitmap.frequencies["aa"] = 10
        self.bitmap.frequencies["ab"] = 3
        self.bitmap.frequencies["bb"] = 5
        self.bitmap.frequencies["ba"] = 0
        
        new_bitmap = TimeseriesBitmap(self.alphabet, self.bitmap.level)
        new_bitmap.frequencies["aa"] = 1
        new_bitmap.frequencies["ab"] = 3
        new_bitmap.frequencies["bb"] = 0
        new_bitmap.frequencies["ba"] = 5
        score = self.bitmap.getAnomalyScore(new_bitmap)        
        self.assertEqual(score, (.8 ** 2 + .3 ** 2 + .5 **2 + 1 ** 2) / 2 ** 2)
        
    def testUpdate(self):
        self.bitmap.window_size = 2
        words = ("aaaaaaaa", "bbbbbbbb", "cccccccc")
        for word in words:
            self.bitmap.update(word)
        self.assertEqual(len(self.bitmap.word_buffer), self.bitmap.window_size)
        self.assertEqual(self.bitmap.frequencies["aa"], 0)
        self.assertEqual(self.bitmap.frequencies["bb"], 7)
        self.assertEqual(self.bitmap.frequencies["cc"], 7)
        

if __name__ == "__main__":
    unittest.main()