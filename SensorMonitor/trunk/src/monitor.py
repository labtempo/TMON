# Includes the lib path
import sys
import tos
import datetime
import time
import logging
from SharedLibs.tools import raw_to_celcius, raw_to_volts_iris, raw_to_volts_micaz

# logging levels
CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.WARNING

RECOGNIZED_MOTES = ['micaz', 'iris']

TEMP_MSG, BATT_MSG, LIGHT_MSG = range(3)
RECOGNIZED_MSG_TYPES = [TEMP_MSG, BATT_MSG, LIGHT_MSG]

logger = None


class TosPacketWrapper(object):
    '''
    Wrapper class for the original tos.Packet to allow inheritance.
    In a second note, tos.Packet is an old-style class (doesn't inherit from object).    
    '''        
    def __init__(self, desc, packet=None):
        self.tos_packet = tos.Packet(desc, packet)        
    
    def __getattr__(self, name):
        # lookup on packet:
        if name in self.tos_packet.__dict__['_names']:
            return self.tos_packet.__dict__['_values'][ self.tos_packet.__dict__['_names'].index(name) ]
        raise AttributeError(name)
    
    def __setattr__(self, name, value):
        if name != 'tos_packet' and name in self.tos_packet.__dict__['_names']:            
            self.tos_packet.__dict__['_values'][ self.tos_packet.__dict__['_names'].index(name) ] = value
        else:
            object.__setattr__(self, name, value)
        

class MultihopSensingMsg(TosPacketWrapper):
    AM_ID = 0x93    
    
    def __init__(self, mote_type, packet=None):
        TosPacketWrapper.__init__(self,
                            [('id',      'int', 2),
                             ('count',   'int', 2),
                             ('reading', 'int', 2),
                             ('type',    'int', 1)],
                            packet)
        if mote_type not in RECOGNIZED_MOTES:
            raise ValueError('Mote type "%s" not recognized' % mote_type)
        self.mote_type = mote_type
    
    def __repr__(self):
        return "<%s id: %s, count: %s, reading: %s, type: %s>" % (type(self).__name__, self.id, self.count, 
                                                                  self.reading, self.type)
    
    def get_value(self):
        value = None
        if self.type == TEMP_MSG:                        
            value = raw_to_celcius(self.reading)
        elif self.type == BATT_MSG:
            if self.reading > 0:
                if self.mote_type == 'iris':
                    value = raw_to_volts_iris(self.reading)
                elif self.mote_type == 'micaz':
                    value = raw_to_volts_micaz(self.reading)
        elif self.type == LIGHT_MSG:
            value = self.reading                         
        else:
            global logger
            logger.warning("Unknown message type %d" % (self.type))   
                            
        return value
    
    
    def is_valid(self):
        '''
        A message is considered valid when at least one of it's attributes does not match it's expected class. 
        '''
        return  isinstance(self.tos_packet.id, (int, long)) and isinstance(self.tos_packet.count, (int, long)) and \
                isinstance(self.tos_packet.reading, (int, long)) and self.tos_packet.type in RECOGNIZED_MSG_TYPES and \
                self.mote_type in RECOGNIZED_MOTES
    

class CTPDebugMsg(TosPacketWrapper):
    AM_ID = 0x72 # 114 in decimal
    
    NET_C_FE_RCV_MSG =  0x21 # This type of message is sent every time a packet is received    
    NET_C_TREE_SENT_BEACON = 0x33 # Indicates that a beacon was sent from the basestation
    NET_C_FE_LOOP_DETECTED = 0x18
    NET_C_FE_NO_ROUTE = 0x12
    NET_C_TREE_NEW_PARENT = 0x31
        
    '''
    Dictionary that holds a short description of some message types
    '''
    MSG_DESC = {NET_C_FE_RCV_MSG: "Packet received.", NET_C_TREE_SENT_BEACON: "Beacon sent.", \
                NET_C_FE_LOOP_DETECTED: "CTP has detected a loop.", NET_C_FE_NO_ROUTE: "No route.", \
                NET_C_TREE_NEW_PARENT: "New parent."}
    
    '''
    A list of messages that won't generate log warnings (everything else will).
    '''
    MSG_BLACK_LIST = [NET_C_FE_RCV_MSG, NET_C_TREE_SENT_BEACON]
        
    '''
    NET_C_DEBUG_STARTED = 0xDE,

    NET_C_FE_MSG_POOL_EMPTY = 0x10,    //::no args
    NET_C_FE_SEND_QUEUE_FULL = 0x11,   //::no args
    NET_C_FE_NO_ROUTE = 0x12,          //::no args
    NET_C_FE_SUBSEND_OFF = 0x13,
    NET_C_FE_SUBSEND_BUSY = 0x14,
    NET_C_FE_BAD_SENDDONE = 0x15,
    NET_C_FE_QENTRY_POOL_EMPTY = 0x16,
    NET_C_FE_SUBSEND_SIZE = 0x17,
    NET_C_FE_LOOP_DETECTED = 0x18,
    NET_C_FE_SEND_BUSY = 0x19,

    NET_C_FE_SENDQUEUE_EMPTY = 0x50, <<
    NET_C_FE_PUT_MSGPOOL_ERR = 0x51,
    NET_C_FE_PUT_QEPOOL_ERR = 0x52,
    NET_C_FE_GET_MSGPOOL_ERR = 0x53,
    NET_C_FE_GET_QEPOOL_ERR = 0x54,
    NET_C_FE_QUEUE_SIZE=0x55,

    NET_C_FE_SENT_MSG = 0x20,  //:app. send       :msg uid, origin, next_hop
    NET_C_FE_RCV_MSG =  0x21,  //:next hop receive:msg uid, origin, last_hop
    NET_C_FE_FWD_MSG =  0x22,  //:fwd msg         :msg uid, origin, next_hop
    NET_C_FE_DST_MSG =  0x23,  //:base app. recv  :msg_uid, origin, last_hop
    NET_C_FE_SENDDONE_FAIL = 0x24,
    NET_C_FE_SENDDONE_WAITACK = 0x25,
    NET_C_FE_SENDDONE_FAIL_ACK_SEND = 0x26,
    NET_C_FE_SENDDONE_FAIL_ACK_FWD  = 0x27,
    NET_C_FE_DUPLICATE_CACHE = 0x28,  //dropped duplicate packet seen in cache
    NET_C_FE_DUPLICATE_QUEUE = 0x29,  //dropped duplicate packet seen in queue
    NET_C_FE_DUPLICATE_CACHE_AT_SEND = 0x2A,  //dropped duplicate packet seen in cache
    NET_C_FE_CONGESTION_SENDWAIT = 0x2B, // sendTask deferring for congested parent
    NET_C_FE_CONGESTION_BEGIN = 0x2C, // 
    NET_C_FE_CONGESTION_END = 0x2D, // congestion over: reason is arg;
                                    //  arg=1 => overheard parent's
                                    //           ECN cleared.
                                    //  arg=0 => timeout.
    NET_C_FE_CONGESTED = 0x2E,

    NET_C_TREE_NO_ROUTE   = 0x30,   //:        :no args
    NET_C_TREE_NEW_PARENT = 0x31,   //:        :parent_id, hopcount, metric   <<
    NET_C_TREE_ROUTE_INFO = 0x32,   //:periodic:parent_id, hopcount, metric
    NET_C_TREE_SENT_BEACON = 0x33,
    NET_C_TREE_RCV_BEACON = 0x34,

    NET_C_DBG_1 = 0x40,             //:any     :uint16_t a
    NET_C_DBG_2 = 0x41,             //:any     :uint16_t a, b, c
    NET_C_DBG_3 = 0x42,             //:any     :uint16_t a, b, c
    '''
    def __init__(self, packet = None):
        TosPacketWrapper.__init__(self   ,
                                [('type' ,      'int', 1),
                                 ('data' ,   'blob', None),
                                 ('seqno', 'int', 2)],
                                packet)
    
    def process(self):
        global logger
        
        if self.type != CTPDebugMsg.NET_C_FE_RCV_MSG:            
            desc = CTPDebugMsg.MSG_DESC.get(self.type, None)
                        
            if self.type not in CTPDebugMsg.MSG_BLACK_LIST:
                logger.warning("CTP DebugMsg %03d: type = 0x%x, data = %s: %s" % (self.seqno, self.type, self.data, desc))
            else:                            
                if desc is None:
                    # general handling (no desc)
                    logger.info("CTP DebugMsg %03d: type = 0x%x, data = %s" % (self.seqno, self.type, self.data))
                else:
                    # general handling (with desc)                 
                    logger.info("CTP DebugMsg %03d: type = 0x%x, data = %s: %s" % (self.seqno, self.type, self.data, desc))


def create_logger(filename):
    global logger
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(CONSOLE_LOG_LEVEL)
    formatter = logging.Formatter(datefmt='%H:%M:%S',fmt="%(asctime)s : %(name)-18s: %(levelname)-8s: %(message)s")
    ch.setFormatter(formatter)
    
    fh = logging.FileHandler(filename)
    fh.setLevel(FILE_LOG_LEVEL)
    formatter = logging.Formatter(fmt="%(asctime)s: %(name)-18s: %(levelname)-8s: %(message)s")
    fh.setFormatter(formatter)   
    
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger


def save_reading(value, msg, timestamp, f_temp, f_batt, f_light):
    global logger
    if msg.is_valid() and isinstance(value, (int, long, float)):        
        if msg.type == TEMP_MSG:
            f_temp.write("%f %d %d %f\n" % (timestamp, msg.id, msg.count, value))
            f_temp.flush()
            logger.info("Mote %d: temperature: %f" % (msg.id, value))
        elif msg.type == BATT_MSG:
            f_batt.write("%f %d %d %f\n" % (timestamp, msg.id, msg.count, value))
            f_batt.flush()
            logger.info("Mote %d: voltage: %f" % (msg.id, value))
        elif msg.type == LIGHT_MSG:
            f_light.write("%f %d %d %d\n" % (timestamp, msg.id, msg.count, value))
            f_light.flush()
            logger.info("Mote %d: light: %d" % (msg.id, value))
        '''
        @note: there is no need to test invalid msg.types, since msg.is_valid takes care of this. 
        '''
    else:        
        logger.warning("Received value (%s) is invalid or the received msg (%s) is invalid." % (value, msg))
            

def new_multihopsensing_packet(data, mote_type):
    msg = None                                   
    if data:
        try:                              
            msg = MultihopSensingMsg(mote_type, data) # convert a packet
        except:
            global logger
            logger.exception("Unable to convert packet. Is this the right format?")
    return msg


def main(args):
    global logger
    
    if '-h' in args or len(args) < 4:
        '''
        If you are wondering where is the first parameter (e.g. serial@/dev/ttyUSB0:57600) parsed,
        it is inside tos (when you import it). 
        '''
        print "Usage: python %s serial@/dev/ttyUSB1:57600 {message_type (e.g. 0x95)} {mote_type (micaz/iris)} [ignore list]" % (args[0])
        sys.exit()    
           
    MultihopSensingMsg.AM_ID = int(args[2], 16)
    
    mote_type = args[3].strip()
    if not mote_type in RECOGNIZED_MOTES:
        print 'Unrecognized mote "%s"' % mote_type
        exit()
        
    motes_to_ignore = []
    if len(args) >= 5:
        motes_to_ignore = map(int, args[4].split(','))
    
    exp_start = datetime.datetime.now().strftime("%d_%m_%y_%Hh%Mm%Ss")
    f_temp = open("../output/temps_%s.txt" % exp_start, "w")
    f_batt = open("../output/batts_%s.txt" % exp_start, "w")
    f_light = open("../output/light_%s.txt" % exp_start, "w")
    logger = create_logger("../output/log/log_%s.txt" % (exp_start))
    
    '''
    Contains a list of every mote. 
    '''
    motes = set()
    
    try:
        am = tos.AM()
        logger.warning("Starting...")
        
        while True:
            p = am.read() # get a packet
            if p and p.type == MultihopSensingMsg.AM_ID: # it is a MultihopSensing packet                
                now = time.time()
                
                msg = new_multihopsensing_packet(p.data, mote_type)
                
                if msg and msg.id not in motes_to_ignore:                                        
                    value = msg.get_value()                    
                    save_reading(value, msg, now, f_temp, f_batt, f_light)
                    
                    '''
                    Detect new motes as they appear on the network
                    '''
                    last_len = len(motes)
                    motes.add(msg.id)
                    curr_len = len(motes)
                    if last_len < curr_len:
                        logger.warning("Mote %d entered the network!" % msg.id)
            else:
                if p and p.type == CTPDebugMsg.AM_ID:                    
                    msg = CTPDebugMsg(p.data)
                    msg.process()
                else:
                    logger.warning("Skipping packet %s" % p)
    except KeyboardInterrupt:
        logger.warning("Aborting...")
    except SystemExit:
        pass # nothing to say about system exit
    except:
        logger.exception("An unhandled exception occurred.")
    finally:
        if f_temp:
            f_temp.close()
        if f_batt:
            f_batt.close()
        if f_light:
            f_light.close()
        logger.warning("Done...")


if __name__ == "__main__":
    main(sys.argv)