'''
Created on Aug 8, 2012

@author: Giulio
'''
import unittest
import col2arff

class TestFunctions(unittest.TestCase):
    def testOutputFilename(self):
        # test .txt input
        input_filename = "my_input.txt"
        output = col2arff.get_output_filename(input_filename)
        self.assertEqual(output, "my_input.arff")
        
        # test .txt.gz
        input_filename = "my_input.txt.gz"
        output = col2arff.get_output_filename(input_filename)
        self.assertEqual(output, "my_input.arff")
        
        # test mixed input
        input_filename = "my_input.txt.gz.arff.intercept"
        output = col2arff.get_output_filename(input_filename)
        self.assertEqual(output, "my_input.arff")

    
class TestFullExecution(unittest.TestCase):
    def testMain(self):
        # regular call
        col2arff.main('col2arff col2arff_test.txt'.split())
        
        # optional parameter
        col2arff.main('col2arff col2arff_test.txt -i 234'.split())
        
        # invalid file
        self.assertRaises(IOError, col2arff.main, 'col2arff invalid.txt'.split())
        
        # not enough parameters
        self.assertRaises(SystemExit, col2arff.main, ['col2arff'])
        
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()