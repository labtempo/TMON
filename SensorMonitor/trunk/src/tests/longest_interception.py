'''
Created on Jul 4, 2012

@author: Giulio
'''
import unittest
import os, sys, cStringIO

lib_path = os.path.abspath('../..')
sys.path.insert(0, lib_path)

# pylint: disable=F0401
import src.longest_interception as li #@UnresolvedImport

class Test(unittest.TestCase):
    def test_main(self):
        # typical call
        # Usage: python %s {max latency} [-f input filename (default is stdin)] [-i ignore-list]
        
        fake_stdin = cStringIO.StringIO()
        real_stdin = sys.stdin
        sys.stdin = fake_stdin
        
        try:        
            # read from stdin
            try:
                li.main(["program", "60"])
            except SystemExit:
                pass
            else:
                self.fail()
            
            # read from stdin and some motes to ignore            
            self.assertRaises(SystemExit, li.main, ["program", "30", "-i", "123,34"])
            
            # missing parameters
            self.assertRaises(SystemExit, li.main, args=["program"])
                 
            # file mode
            li.main(["program", "60", "-f", "../../tests/input_longest_interception.txt"])
        finally:
            sys.stdin = real_stdin


    def test_longest_interception(self):
        output = li.main(["program", "600", "-f", "../../tests/input_longest_interception.txt"])        
        self.assertEquals((1337969475.114938, 1337969485.114938), output)
    
    
    def test_greatest_intersection(self):        
        intervals_to_check = [ [(1, 5), (6, 10), (10, 15)], [(3, 7), (8, 12)], [(5, 7), (8, 11)] ]
        interval = (1, 5)
        oracle = (5, 5)
        
        output = li.greatest_intersection(interval, intervals_to_check, row=1)
        self.assertEquals(oracle, output)
        
        interval = (6, 10)
        oracle = (8, 10)
        output = li.greatest_intersection(interval, intervals_to_check, row=1)
        self.assertEquals(oracle, output)
        
        interval = intervals_to_check[0][2]
        oracle = (10, 11)
        output = li.greatest_intersection(interval, intervals_to_check, row=1)
        self.assertEquals(oracle, output)
                        
        intervals_to_check = [ [(68, 87)], [(75, 85)], [(71, 86)] ]
        interval = intervals_to_check[0][0]
        oracle = (75, 85)
        
        output = li.greatest_intersection(interval, intervals_to_check, row=1)
        self.assertEquals(oracle, output)
        
    def test_read_intervals(self):
        output = li.read_intervals(input_filename="../../tests/input_longest_interception.txt", \
                                   motes_to_ignore=[], max_latency=60)        
        oracle = [[[1337969468.114938, 1337969487.114938]], [[1337969475.114938, 1337969485.114938]], \
                  [[1337969471.114938, 1337969486.114938]]]
        self.assertEquals(oracle, output)
        
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()