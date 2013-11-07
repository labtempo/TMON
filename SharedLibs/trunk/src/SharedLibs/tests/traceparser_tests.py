'''
Created on Aug 11, 2012

@author: Giulio
'''
import unittest
import SharedLibs.tracetools as tp
from SharedLibs.tools import parse_line, parse_arff_file
from SharedLibs import tracetools
from collections import OrderedDict
import tempfile
import os

class TestTraceReader(unittest.TestCase):
    def setUp(self):
        self.parser = tp.TraceReader("trace_test.txt")
    
    def tearDown(self):
        self.parser.close()
    
    def testGetFileType(self):
        filename = "my_file.txt"
        output = tp.extract_file_type(filename)
        oracle = "txt"
        self.assertEqual(oracle, output)
        
        filename = "my_file.txt.gz"
        output = tp.extract_file_type(filename)
        oracle = "txt"
        self.assertEqual(oracle, output)
        
        filename = "my_file.arff"
        output = tp.extract_file_type(filename)
        oracle = "arff"
        self.assertEqual(oracle, output)
        
        filename = "my_file.txt.gz.arff"
        output = tp.extract_file_type(filename)
        oracle = "arff"
        self.assertEqual(oracle, output)
        
        # full path
        filename = "/home/dir/my_file.arff"
        output = tp.extract_file_type(filename)
        oracle = "arff"
        self.assertEqual(oracle, output)
        
        # full path with dots
        filename = "../my_file.arff"
        output = tp.extract_file_type(filename)
        oracle = "arff"
        self.assertEqual(oracle, output)
        
    
    def testParseColFile(self):
        gen = self.parser.parse()
        self.assertTrue(isinstance(gen, type((i for i in range(2)))))
        
        # test txt file
        output = [values for values in gen]
        oracle = []
        f = open("trace_test.txt")
        try:
            for line in f:
                oracle.append(parse_line(line))
        finally:
            f.close()
        self.assertEqual(oracle, output)
    
    
    @unittest.skip("Maybe oracle is not trustworthy")
    def testParseArffFile(self):    
        # test arff file
        self.parser = tp.TraceReader("trace_test.arff")
        gen = self.parser.parse()
        output = [values for values in gen]
        self.parser.close()
        
        oracle = []
        f = open("trace_test.arff")
        try:
            for data in parse_arff_file(iter(f)):
                oracle.append(data)
        finally:
            f.close()
        self.assertEqual(len(oracle), len(output))        
        self.assertEqual(oracle, output)                
        
    
    def testRawAggregateFile(self):
        self.parser = tp.TraceReader("trace_test.agg")
        gen = self.parser.parse()
        output = [values for values in gen]
        self.parser.close()
        
        oracle = [ (1349364575.434680,237, 0, 27.086772, 76, 3.124826),\
                   (1349364575.503515,237, 0, 27.086772, 76, 3.124826),\
                   (1349364575.630907,248, 0, 32.316614, 515, 3.242182),\
                   (1349364575.745322,239, 0, 26.399825, 44, 3.116148),\
                   (1349364575.970389,245, 0, 26.301951, 498, 3.186947),\
                   (1349364576.040562,216, 0, 31.597115, 523, 3.168949),\
                   (1349364576.173389,216, 0, 31.597115, 523, 3.168949),\
                   (1349364577.237405,219, 0, 40.350718, 534, 3.124826),\
                   (1349364577.314838,217, 0, 36.876537, 290, 3.023758),\
                   (1349364577.383776,252, 0, 42.937803, 275, 3.040149),\
                   (1349364577.452631,233, 0, 47.707470, 194, 3.124826),\
                   (1349364577.547215,233, 0, 47.707470, 194, 3.124826),\
                   (1349364578.059417,233, 0, 47.707470, 194, 3.124826),\
                ]
        
        self.assertEqual(oracle, output)
    
    
    def _testSupressRepetitions(self):
        self.parser = tp.TraceReader("trace_test_repetitions.txt", supress_repetitions=True)
        output = [values for values in self.parser.parse()]
        oracle = [(1341607696.752916,134,18381,11.218947), (1341607697.512910,225,0,24.259934), \
                  (1341607697.832944,225,1,29.670462)]
        self.assertEqual(oracle, output)
    
    
    @unittest.skip("Not implemented")
    def testSupressMiddleRepetitions(self):
        '''
        This functionality works as follows:
            The parser detects a repetition and suppress it, just like supress_repetitions.
            But, as soon it finds out that the value has changed, it outputs the past suppressed value
            and then, immediately afterwards, the new value.
            This is incredibly useful to plotting.  
        '''
        pass
    
    
    def testSupressRapidChanges(self):
        '''
        Ommit a change to the value of a mote if it changes too fast.
        '''
        self.parser = tp.TraceReader("test_rapid_changes.txt", suppress_rapid_changes=True)
        gen = self.parser.parse()
        self.assertTrue(isinstance(gen, type((i for i in range(2)))))
        
        # test txt file
        output = [values for values in gen]
        oracle = [(1341607696.752916, 134, 18381, 11.218947),
                  (1341607697.832944, 248, 1537, 29.670462), \
                  (1341607697.853437, 249, 1210, 27.086772), \
                  (1341607699.753355, 134, 18382, 11.511165), \
                  (1341607701.283434, 241, 1159, 25.132156), \
                  (1341607701.753172, 134, 18384, 10.142534), \
                  (1341607702.712892, 245, 1379, 24.937975), \
                  (1341607702.753301, 134, 18385, 10.730671), \
                  (1341607703.753879, 134, 18386, 11.316414), \
                  ]
        self.assertEqual(oracle, output)
    
    
    def testAutomaticTimestamps(self):
        '''
        Test automatic creation of timestamps on arff files that doesn't have them.
        '''
        self.parser = tp.TraceReader("trace_test_nots.arff", auto_timestamps=True)
        output = [tuple(d.values()) for d in self.parser.parse()]
        oracle = [(1, 24.163262,20.421106,32.007574,24.550229,24.744001,21.663573,18.133233,39.550011,20.612037,23.680575), \
                  (2, 24.163262,20.421106,32.007574,24.550229,24.840963,21.663573,18.228512,39.550011,20.612037,23.680575), \
                  (3, 24.163262,20.421106,32.007574,24.550229,24.840963,21.759307,18.228512,39.550011,20.612037,23.680575), \
                  (4, 24.163262,20.421106,32.007574,24.550229,24.840963,21.759307,18.133233,39.550011,20.612037,23.680575), \
                  (5, 24.163262,20.421106,32.007574,24.550229,24.840963,21.759307,18.133233,39.550011,20.612037,23.680575)]
        self.assertEqual(output, oracle)
        self.assertTrue("timestamp" in self.parser.arff_attributes)
    
    
    def _testAutomaticInterpolation(self):
        '''
        Test automatic interpolation of missing data
        '''
        self.parser = tp.TraceReader("trace_test_missing_data.arff", auto_interpolation=True)
        output = [d['timestamp'] for d in self.parser.parse()]
        pred_ts = output[0]
        for val in output:
            self.assertEqual(val, pred_ts)
            pred_ts += 1
           
            
        

class TestTraceWriter(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(tempfile.gettempdir(), "output.txt")
        self.tw = tracetools.TraceWriter(self.filename)
    
    def tearDown(self):
        self.tw.close()
    
    def testCreation(self):
        self.assertEqual(self.tw.output_type, "txt")
    
    def testOutputType(self):
        # txt
        self.assertEqual(self.tw.output_type, "txt")
        
        # arff
        filename = "output.arff"
        self.tw = tracetools.TraceWriter(filename, arff_attributes=["attr1", "attr2"])
        self.assertEqual(self.tw.output_type, "arff")
    
    def testSetArffAttributes(self):
        arff_attributes = ["attr1", "attr2"]
        
        # arff with attributes
        self.tw = tracetools.TraceWriter("filename.arff", arff_attributes=arff_attributes)
        
        # arff with no attributes
        self.assertRaises(tracetools.TraceWriterException, tracetools.TraceWriter, "filename.arff")
        
        # attributes but not arff
        self.assertRaises(tracetools.TraceWriterException, tracetools.TraceWriter, "filename.txt", \
                          arff_attributes=arff_attributes)
        
        self.assertEqual(self.tw.arff_attributes, arff_attributes)
    
    def testWriteConsistency(self):
        # txt        
        line1 = (100.0, 1, 1, 25.6)
        self.tw.write(line1)
        line2 = (101.0, 2, 2, 23.0)
        self.tw.write(line2)
        self.tw.close()
        
        tr = tracetools.TraceReader(self.filename)
        file_contents = [d for d in tr.parse()]
        tr.close()
        
        self.assertEqual(file_contents, [line1, line2])
        
        # arff
        self.tw = tracetools.TraceWriter("output.arff", ["timestamp", "mote_1", "mote_2"])        
        data = OrderedDict()
        data["timestamp"] = 100.0
        data["mote_1"] = 25.6
        data["mote_2"] = 23.0
        self.tw.write(data)
        self.tw.close()
        
        tr = tracetools.TraceReader("output.arff")
        file_contents = [d for d in tr.parse()]
        
        self.assertEqual(file_contents, [data])


class TestTraceAdapterRaw2Arff(unittest.TestCase):
    def setUp(self):
        self.parser = tp.TraceReader("trace_test.txt")
        self.adapter = tp.TraceAdapter(self.parser, out_format=tp.UNIFORM_FILE_FORMAT)        
    
    def test_creation(self):
        pass
    
    def testUpdate(self):
        mote_id = 20
        stacks = {20: [], 13: [], 15: []}
        data = 25.3
        self.adapter.parser._update_stacks(mote_id, stacks, data)        
        self.assert_(data in stacks[mote_id], msg="data must be inside stack after update")
        
        data = 27
        self.adapter.parser._update_stacks(mote_id, stacks, data)        
        self.assert_(data == stacks[mote_id].pop(), msg="data must be inserted on the back of the stack")
        
        stacks[mote_id].pop()        
        self.assert_(not any(stacks.values()), msg="all data must be purged by now")
    
    
    def testUpdateUnrecognizedMote(self):
        mote_id = 25
        stacks = {20: [], 13: [], 15: []}
        data = 25.3
        # an unrecognized mote should lead to an error
        self.assertRaises(tp.TraceParserException, self.adapter.parser._update_stacks, mote_id, stacks, data)
        
    
    def testConvertEmptyStacks(self):
        stacks = {20: [(2,3)], 13: [(3,3)], 15: []}
        output = self.adapter.parser._join_stacks(stacks, 1)
        self.assertEquals(output, [], msg="Should give an empty tuple when at least one of the stacks is empty. Instead, we got '%s'" % str(output))
        self.assertEquals([[(2, 3)], [(3, 3)], []], stacks.values(), msg="The stacks should remain intact.")
        
        stacks = {20: [(1, 2)], 13: [(1, 3)], 15: [(1, 5)]}
        output = self.adapter.parser._join_stacks(stacks, 1)
        self.assertEquals(output, [1, 2, 3, 5], \
                          msg="Should give a tuple when none of the stacks are empty. Instead, we got '%s'" % str(output))
            
    
    def testConvertUnsynchronizedStacks(self):
        stacks = {20: [(1, 2)], 13: [(2, 3)], 15: [(3, 5)]}
        output = self.adapter.parser._join_stacks(stacks, 1)
        self.assertEquals(output, [1, 2, 3, 5], \
                          msg="Should give an empty tuple when not synchronized. Instead, we got '%s'" % str(output))
            
    def test_parse(self):                
        gen = self.adapter.parse()
        self.assertTrue(isinstance(gen, type((i for i in range(2)))))
        
        empty = True                
        # test txt file
        for val in gen:
            empty = False            
            if not isinstance(val, dict):
                self.fail("Must be a dict.")
            self.assertTrue("timestamp" in val.keys())
            self.assertTrue("mote_134" in val.keys())
            self.assertTrue("mote_245" in val.keys())
        
        if empty:
            self.fail("Empty generator")
        
    def getAllTuples(self, stacks, curr_time=1, iterations=0):
        if iterations == 0:
            iterations = min(map(len, stacks.values()))
        result = []
        for _ in xrange(iterations):
            output = self.adapter.parser._join_stacks(stacks, curr_time)
            result.append(output)
            curr_time += 1
        return result
    
    def testExampleSynchronized(self):        
        stacks = {20: [(1, 4), (2, 5), (3, 6)], 13: [(1, 3), (2, 3), (3, 4)], 15: [(1, 5), (2, 5), (3, 3)]}                        
        oracle = [[1, 4, 3, 5], [2, 5, 3, 5], [3, 6, 4, 3]]
        result = self.getAllTuples(stacks)
        self.assertEqual(oracle, result)    
    
    def testExampleSynchronizedMissingData(self):
        stacks = {20: [(1, 4), (2, 5)], 13: [(1, 3), (2, 3), (3, 4)], 15: [(1, 5), (2, 5), (3, 3)]}
        oracle = [[1, 4, 3, 5], [2, 5, 3, 5]]
        result = self.getAllTuples(stacks)
        self.assertEqual(oracle, result)
    
    def testExampleUnsynchronized(self):
        stacks = {20: [(1, 4), (2, 5), (3, 6)], 13: [(0.5, 3), (2, 3), (3, 4)], 15: [(1.5, 5), (2, 5), (3, 3)]}
        oracle = [[1, 4, 3, 5], [2, 5, 3, 5], [3, 6, 4, 3]]
        result = self.getAllTuples(stacks)
        self.assertEqual(oracle, result)
    
    def testExampleOldData(self):
        stacks = {20: [(1, 4), (2, 5), (3, 6)], 13: [(1, 3), (2, 3), (3, 4)], 15: [(1, 5), (2, 5), (3, 3)]}                        
        oracle = [[2, 5, 3, 5], [3, 6, 4, 3]]
        result = self.getAllTuples(stacks, 2, iterations=2)
        self.assertEqual(oracle, result)  


class TestTraceAdapterRawAggregate2Raw(unittest.TestCase):
    def setUp(self):
        self.parser = tp.TraceReader("trace_test.agg")
        attribute = tp.TEMP
        self.adapter = tp.TraceAdapter(self.parser, tp.RAW_FILE_FORMAT, attribute)
    
    def test_creation(self):
        pass
    
    def test_parse(self):
        oracle = [ (1349364575.434680,237, 0, 27.086772),\
                   (1349364575.503515,237, 0, 27.086772),\
                   (1349364575.630907,248, 0, 32.316614),\
                   (1349364575.745322,239, 0, 26.399825),\
                   (1349364575.970389,245, 0, 26.301951),\
                   (1349364576.040562,216, 0, 31.597115),\
                   (1349364576.173389,216, 0, 31.597115),\
                   (1349364577.237405,219, 0, 40.350718),\
                   (1349364577.314838,217, 0, 36.876537),\
                   (1349364577.383776,252, 0, 42.937803),\
                   (1349364577.452631,233, 0, 47.707470),\
                   (1349364577.547215,233, 0, 47.707470),\
                   (1349364578.059417,233, 0, 47.707470),\
                ]
        
        output = [data for data in self.adapter.parse()]        
        self.assertEqual(oracle, output)

