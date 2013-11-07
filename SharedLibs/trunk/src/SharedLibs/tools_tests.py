import unittest
from tools import *
from TOSSIM import *


class TestFunctions(unittest.TestCase):
    
    def assertEqualTopologies(self, oracle, output):
        oracle = oracle.strip().splitlines()
        output = output.splitlines()
        self.assertEquals(len(output), len(oracle))
        for out_line, oracle_line in zip(output, oracle):
            self.assertEquals(out_line, oracle_line.strip())
    
    def test_create_topology_trivial(self):
        t = Tossim([])
        output = create_complete_topology(range(3), None, -66).getvalue()
        oracle = \
        """
        0 1 -66.000000
        0 2 -66.000000
        1 0 -66.000000
        1 2 -66.000000
        2 0 -66.000000
        2 1 -66.000000
        """
        self.assertEqualTopologies(oracle, output)
        
    
    def test_create_topology_non_default_gains(self):       
        gains = {(0, 1): -100, (2, 0): -140} 
        output = create_complete_topology(range(3), gains, -66).getvalue()
        oracle = \
        """
        0 1 -100.000000
        0 2 -66.000000
        1 0 -66.000000
        1 2 -66.000000
        2 0 -140.000000
        2 1 -66.000000
        """
        self.assertEqualTopologies(oracle, output)
    
    
    def test_read_topology_from_memory(self):
        t = Tossim([])        
        node_count = 3
        topo = create_complete_topology(range(node_count), None, -66)
        nodes = read_topology(topo, t)
        self.assertEquals(len(nodes), node_count)
        for i in range(node_count):
            self.assertEquals(nodes[i].id(), i)
    

if __name__ == '__main__':
    unittest.main()
