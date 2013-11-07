'''
Created on Jun 20, 2012

@author: giulio
'''
import unittest
import sys, os, cStringIO

lib_path = os.path.abspath('../..')
sys.path.insert(0, lib_path)

# pylint: disable=F0401
import src.network_simulation as net #@UnresolvedImport


class TestNaive(unittest.TestCase):
    def setUp(self):
        self.topology_filename = "../../tests/topology.txt"
        self.temp_filename = "../../tests/test_temp.txt"
    
    def test_main(self):
        # not enough args
        try:
            net.main(["script"])
        except SystemExit:
            pass # don't let the program finish
        else:
            self.fail("Expected SystemExit")
        
        # -h switch is present
        try:
            net.main(["script", "-h"])
        except SystemExit:
            pass # don't let the program finish
        else:
            self.fail("Expected SystemExit")
        
        # typical call
        net.main(["script", self.temp_filename, "-t", self.topology_filename])
        
        # typical call with automatic topology
        net.main(["script", self.temp_filename])
        
    def test_read_topology(self):
        basestation = net.BaseStation(None)
        output = net.read_topology(self.topology_filename, basestation)
        oracle = {0: [1, 2], 1: [2], 2: [1]} # nodes: 0, 1
        
        self.assertEquals(len(oracle.values()), len(output.values()))
        
        for node_id, node in output.items():
            self.assertEquals(oracle[node_id], [n.node_id for n in node.neighbors])
    
    def test_receive_basestation(self):
        reading = net.ReadingMessage(timestamp=32.5, node_id=0, value=25.0, counter=0)        
        test_file = cStringIO.StringIO()
        basestation = net.BaseStation(test_file)
        basestation.receive(reading)
        
        # unknown message
        reading = net.Message()        
        test_file = cStringIO.StringIO()
        basestation = net.BaseStation(test_file)
        self.assertRaises(Exception, basestation.receive, reading)
            
    def test_feed_node(self):
        reading = net.ReadingMessage(timestamp=32.5, node_id=0, value=25.0, counter=0)        
        test_file = cStringIO.StringIO()
        basestation = net.BaseStation(test_file)
        node = net.SensorNode(reading.node_id, basestation)
        node.feed_reading(reading)
        
        test_file.flush()
        test_file.reset()
        
        output = test_file.read()
        oracle = "32.500000 0 0 25.000000\n" 
        
        self.assertEquals(output, oracle)
    
    def test_auto_topology(self):        
        basestation = net.BaseStation(None)
        
        node_0 = net.SensorNode(0, basestation)
        node_1 = net.SensorNode(1, basestation)
        
        nodes = {0: node_0, 1: node_1}
        
        node_2 = net.auto_update_topology(2, nodes, basestation)
        
        self.assertTrue(isinstance(node_2, net.SensorNode))        
        self.assertEquals(node_2.neighbors, set([node_0, node_1]))
        self.assertEquals(node_0.neighbors, set([node_2]))
        self.assertEquals(node_1.neighbors, set([node_2]))
        

class TestAdditive(unittest.TestCase):
    def setUp(self):
        self.topology_filename = "../../tests/topology.txt"
        self.temp_filename = "../../tests/test_temp.txt"
    
    def feed_reading(self, node):
        reading = net.ReadingMessage(timestamp=32.5, node_id=0, value=25.0, counter=0)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=33.5, node_id=0, value=25.0, counter=1)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=34.5, node_id=0, value=26.0, counter=2)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=35.5, node_id=0, value=27.0, counter=3)
        node.feed_reading(reading)
    
    def feed_reading_bigger(self, node):
        reading = net.ReadingMessage(timestamp=32.5, node_id=0, value=25.0, counter=0)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=33.5, node_id=0, value=25.0, counter=1)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=34.5, node_id=0, value=26.0, counter=2)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=35.5, node_id=0, value=27.0, counter=3)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=36.5, node_id=0, value=25.0, counter=4)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=37.5, node_id=0, value=25.0, counter=5)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=38.5, node_id=0, value=26.0, counter=6)
        node.feed_reading(reading)
        
        reading = net.ReadingMessage(timestamp=39.5, node_id=0, value=27.0, counter=7)
        node.feed_reading(reading)
    
    def test_main(self):
        # typical call
        net.main(["script", self.temp_filename, "-t", self.topology_filename,  "-m", "additive", "1", "10", "1"])
        
        # missing all parameters
        self.assertRaises(net.GenericException, net.main, \
                          ["script", self.temp_filename, "-t", self.topology_filename, "-m"])
        
        # missing some parameters
        self.assertRaises(net.GenericException, net.main, \
                          ["script", self.temp_filename, "-t", self.topology_filename, "-m", "additive"])
        
        # missing some parameters
        self.assertRaises(net.GenericException, net.main, \
                          ["script", self.temp_filename, "-m", "additive", "1"])
    
    def test_feed_node(self):                
        test_file = cStringIO.StringIO()
        basestation = net.BaseStation(test_file)
        node = net.AdditiveSensorNode(0, basestation, 1, 10, 1)
        
        self.feed_reading(node)
        
        test_file.flush()
        test_file.reset()
        
        output = test_file.read()
        oracle = "32.500000 0 0 25.000000\n35.500000 0 3 27.000000\n"
        
        self.assertEquals(output, oracle)    
    
    
    def test_feed_node_as_naive(self):
        test_file = cStringIO.StringIO()
        basestation = net.BaseStation(test_file)
        node = net.AdditiveSensorNode(0, basestation, 1, 1, 1)
        
        self.feed_reading(node)
                
        test_file.flush()
        test_file.reset()
        
        output = test_file.read()
        oracle = "32.500000 0 0 25.000000\n33.500000 0 1 25.000000\n34.500000 0 2 26.000000\n35.500000 0 3 27.000000\n"
        
        self.assertEquals(output, oracle)
    
    
    def test_feed_node_as_naive_2(self):
        test_file = cStringIO.StringIO()
        basestation = net.BaseStation(test_file)
        node = net.AdditiveSensorNode(0, basestation, 2, 2, 2)
        
        self.feed_reading_bigger(node)        
                
        test_file.flush()
        test_file.reset()
        
        output = test_file.read()
        oracle = "32.500000 0 0 25.000000\n34.500000 0 2 26.000000\n36.500000 0 4 25.000000\n38.500000 0 6 26.000000\n"
        
        self.assertEquals(output, oracle)
        
    
    def test_feed_node_incr(self):
        test_file = cStringIO.StringIO()
        basestation = net.BaseStation(test_file)
        node = net.AdditiveSensorNode(0, basestation, 2, 10, 2)
        
        self.feed_reading(node)
        
        test_file.flush()
        test_file.reset()
        
        output = test_file.read()
        oracle = "32.500000 0 0 25.000000\n34.500000 0 2 26.000000\n"
        
        self.assertEquals(output, oracle)
        

class TestDeadzone(unittest.TestCase):
    def setUp(self):
        self.topology_filename = "../../tests/topology.txt"
        self.temp_filename = "../../tests/test_temp.txt"


    def feed_reading(self, node):
        values = [25.0, 26.0, 26.5] + [30.0] * 5 + [25.0, 26.0, 26.5]
        print values
        
        for i in range(len(values)):
            reading = net.ReadingMessage(timestamp=30.5 + i, node_id=0, value=values[i], counter=i)
            node.feed_reading(reading)
        
    def test_feed_node(self):                
        test_file = cStringIO.StringIO()
        basestation = net.BaseStation(test_file)
        node = net.DeadzoneSensorNode(0, basestation, 0.5, 99999)
        self.feed_reading(node)
        self.assertEquals(node.sent_count, 6 + 1)
        
        
if __name__ == "__main__":
    unittest.main()