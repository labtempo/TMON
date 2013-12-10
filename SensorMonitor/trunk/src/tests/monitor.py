'''
Created on Jul 3, 2012

@author: giulio
'''
import unittest, os, sys
import random, logging, cStringIO, time

lib_path = os.path.abspath('../..')
sys.path.insert(0, lib_path)

# pylint: disable=F0401
import src.monitor as mon #@UnresolvedImport


def new_multihopsensing_msg(mote_type=mon.RECOGNIZED_MOTES[0], msg_type=mon.TEMP_MSG, msg_reading=300, msg_id=1, \
                            msg_counter=10):
    msg = mon.MultihopSensingMsg(mote_type)
    msg.type = msg_type
    msg.reading = msg_reading        
    msg.id = msg_id
    msg.count = msg_counter    
    return msg

# pylint: disable=W0102
def new_ctp_msg(msg_type=mon.CTPDebugMsg.NET_C_FE_RCV_MSG, data=[0, 1, 2, 3, 4], seqno=0):
    msg = mon.CTPDebugMsg()
    msg.type = msg_type
    msg.data = data
    msg.seqno = seqno
    return msg

class DummyPacket:
    def __init__(self, t):
        self.type = t    

class TestBasics(unittest.TestCase):
    def testMain(self):
        # not enough parameters
        for i in range(1, 4):
            try:
                mon.main(["text"] * i)
            except SystemExit:
                pass
            else:
                self.fail("SystemExit not raised")
    
    def test_create_logger(self):        
        random_name = "".join(( chr( int(random.random() * (90 - 65) + 65) ) for i in range(10) ))        
        logger = mon.create_logger(random_name)
        self.assertTrue( isinstance(logger, logging.Logger) )        
        self.failUnless(os.path.exists(random_name))        
        if not sys.platform.startswith("win"):
            os.remove(random_name)
        else:
            print "Unable to remove test logger on Windows"

    def test_multihopsensing_temps(self):        
        for mote_type in mon.RECOGNIZED_MOTES:
            for msg_type in mon.RECOGNIZED_MSG_TYPES:
                msg = new_multihopsensing_msg(mote_type=mote_type, msg_type=msg_type)
                value = msg.get_value()
                self.assertTrue( isinstance(value, float) or isinstance(value, int) )
    
    def test_multihopsensing_wrong_type(self):    
        # wrong msg.type: expected value = None
        msg = new_multihopsensing_msg(msg_type=90312)
        value = msg.get_value()                
        self.assertTrue(value is None)
    
    def test_multihopsensing_invalid_mote(self):
        # unrecognized mote: expected value = None
        self.assertRaises(ValueError, new_multihopsensing_msg, {"mote_type":"non existing model", "msg_type":mon.BATT_MSG})        
            
    def test_multihopsensing_invalid_reading(self):
        # reading is out of range: expected value = None
        msg = new_multihopsensing_msg()        
        for test_value in [-300, 0, 15000]:
            msg.reading = test_value  
            value = msg.get_value()
            self.assertTrue(value is None, msg="Value was %s" % str(value))
        
    def test_save_reading(self):        
        '''
        Typical case
        '''
        msg_temp = new_multihopsensing_msg()        
        temp_value = msg_temp.get_value()
        self.assertTrue(isinstance(temp_value, float))
        
        f_temp = cStringIO.StringIO()
        f_batt = cStringIO.StringIO()
        f_light = cStringIO.StringIO()
        timestamp = time.time()
        
        mon.save_reading(temp_value, msg_temp, timestamp, f_temp, f_batt, f_light)
        
        msg_batt = new_multihopsensing_msg(msg_type=mon.BATT_MSG)
        batt_value = msg_batt.get_value()                                        
        mon.save_reading(batt_value, msg_batt, timestamp, f_temp, f_batt, f_light)
        
        msg_light = new_multihopsensing_msg(msg_type=mon.LIGHT_MSG)
        light_value = msg_light.get_value()
        mon.save_reading(light_value, msg_light, timestamp, f_temp, f_batt, f_light)
        
        f_temp.flush()
        f_batt.flush()
        f_light.flush()
        f_temp.reset()
        f_batt.reset()
        f_light.reset()
                
        self.assertEquals(f_temp.read(), "%f %d %d %f\n" % (timestamp, msg_temp.id, msg_temp.count, temp_value))
        self.assertEquals(f_batt.read(), "%f %d %d %f\n" % (timestamp, msg_batt.id, msg_batt.count, batt_value))
        self.assertEquals(f_light.read(), "%f %d %d %d\n" % (timestamp, msg_light.id, msg_light.count, light_value))
        
               
        '''
        Invalid messages
        '''
        invalid_msg = new_multihopsensing_msg(msg_type=None)
        mon.save_reading(light_value, invalid_msg, timestamp, f_temp, f_batt, f_light)
        
        invalid_msg = new_multihopsensing_msg(msg_type=-1)
        mon.save_reading(light_value, invalid_msg, timestamp, f_temp, f_batt, f_light)
           
    
    def test_packet_conversion(self):        
        msg = mon.new_multihopsensing_packet(None, mon.RECOGNIZED_MOTES[0])
        self.assertTrue(msg is None)
                
        self.assertRaises(ValueError, mon.MultihopSensingMsg, ("data"))
    
    def test_msg_is_valid(self):
        msg = mon.MultihopSensingMsg(mon.RECOGNIZED_MOTES[0])
                
        msg.id = 255
        self.assertTrue(not msg.is_valid())
        
        msg.count = 0
        self.assertTrue(not msg.is_valid())
        
        msg.reading = 123
        self.assertTrue(not msg.is_valid())
        
        msg.type = mon.TEMP_MSG        
        self.assertTrue(msg.is_valid())
        
        '''
        Further tests
        '''
        msg = new_multihopsensing_msg(mote_type="iris", msg_type=0, msg_reading=362, msg_id=226, msg_counter=0)
        self.assertTrue(msg.is_valid())
        
        msg = new_multihopsensing_msg(mote_type=mon.RECOGNIZED_MOTES[0], msg_type=mon.TEMP_MSG, msg_reading=300, msg_id=1, \
                            msg_counter=10)        
        self.assertTrue(msg.mote_type == mon.RECOGNIZED_MOTES[0])
        self.assertTrue(msg.type == mon.TEMP_MSG)
        self.assertTrue(msg.reading == 300)
        self.assertTrue(msg.id == 1)
        self.assertTrue(msg.count == 10)
        
        '''
        Invalid battery level
        '''
        msg = new_multihopsensing_msg(mote_type="iris", msg_type=mon.BATT_MSG, msg_reading=0, msg_id=250, \
                            msg_counter=0)
        value = msg.get_value()
        self.assertTrue(msg.is_valid())
        self.assertTrue(value is None)
        
    
    def test_ctp_msg_creation(self):
        # typical
        msg = new_ctp_msg(msg_type="mytype", data="stuff", seqno=32)
        self.assertTrue(isinstance(msg, mon.CTPDebugMsg))
        self.assertTrue(msg.data == "stuff" and msg.type == "mytype" and msg.seqno == 32)
        
        # all invalid
        msg = new_ctp_msg(msg_type=None, data=None, seqno=None)
        self.assertTrue(isinstance(msg, mon.CTPDebugMsg))
        self.assertTrue(msg.data is None and msg.type is None and msg.seqno is None)
    
    
    def test_ctp_msg_process(self):
        '''
        Should process all messages without any errors whatsoever
        '''
        msg = new_ctp_msg()
        for msg_code in mon.CTPDebugMsg.MSG_DESC.keys():
            msg.type = msg_code
            msg.process()
        
        # processing unlisted message
        msg = new_ctp_msg()
        msg.type = -50
        msg.process()
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testMain']
    unittest.main()