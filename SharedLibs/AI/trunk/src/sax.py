import random
import numpy as np
import math


__author__ = "Aleksandar Mastilovic"
__copyright__ = "Copyright 2012, Aleksandar Mastilovic"
__credits__ = ["Aleksandar Mastilovic"]
__version__ = "1.0.1"
__maintainer__ = "Aleksandar Mastilovic"
__email__ = "aleksandar.mastilovic@gmail.com"
__status__ = "Development"


SMALL_VALUE = 0.000001


class SAX(object):

    def __init__(self):
        pass

    def direction(self):
        v = random.randint(0, 1)
        if v == 0:
            return -1
        return 1

    def normalize(self, xs):    
        '''
        Z-normalization
        '''        
        X = np.asanyarray(xs)
        stddev = X.std()
        if stddev == 0:
            return np.zeros(shape=X.shape)
        return (X-X.mean()) / stddev


    def euclidean_dist(self, x1, x2):
        """Euclidean distance of two signals"""
        l_x1, l_x2 = len(x1), len(x2)
        if l_x1 < l_x2:
            x1.extend([0.0 for _ in xrange(l_x2-l_x1)])
        elif l_x2 < l_x1:
            x2.extend([0.0 for _ in xrange(l_x1-l_x2)])

        return np.sqrt(np.sum(np.square(i - j) for i, j in zip(x1, x2)))


    def to_PAA(self, vals, M):
        '''
        @param M: window size
        '''
        n = len(vals)
        step_f = float(n) / M
        step = int(math.ceil(step_f))
        res = []
        loop = 0
        ptr = int(loop * step_f)
        while ptr <= n-step:
            subarr = np.array( vals[ptr:int(ptr+step)] )
            res.append(np.mean(subarr))            
            loop += 1
            ptr = int(loop * step_f)

        return np.array(res)


    def convert(self, vals, alphabet, M=8):
        paa = self.to_PAA(self.normalize(vals), M)        
        max_paa = np.max(paa)
        min_paa = np.min(paa)
        alen = len(alphabet)
        step = max((max_paa - min_paa) / alen, SMALL_VALUE)
        
        def map_to_char(v):            
            idx = int(np.abs(v - min_paa) / step)
            if idx >= alen:
                idx = alen - 1
            return alphabet[idx]

        retval = "".join(map_to_char(v) for v in paa)        

        return retval
