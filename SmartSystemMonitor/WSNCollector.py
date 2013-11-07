# Includes the lib path
import sys
import tos
import datetime
import time
import logging
from SharedLibs.tools import raw_to_celcius, raw_to_volts_iris, raw_to_volts_micaz
from Shared import *
import pika  # component to access Event Manager

# logging levels
CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.WARNING

RECOGNIZED_MOTES = ['micaz', 'iris']

logger = None

class Samples(tos.Packet):
    def __init__(self, payload=None):
        tos.Packet.__init__(self,
                               [('readingTemperature', 'int', 2),
                                ('readingLight', 'int', 2),
                                ('readingVoltage', 'int', 2),
                                ('source', 'int', 2),
                                ('seqno', 'int', 2),
                                ('parent', 'int', 2),
                                ('metric', 'int', 2),
                                ('delay', 'int', 2)],
                                payload)


class CtpData(tos.Packet):
    def __init__(self, payload=None):
        tos.Packet.__init__(self,
                               [('options', 'int', 1),
                                ('thl', 'int', 1),
                                ('etx', 'int', 2),
                                ('origin', 'int', 2),
                                ('originSeqNo', 'int', 1),
                                ('collectionId', 'int', 1),
                                ('data', 'blob', None)],
                               payload)
        
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
            return self.tos_packet.__dict__['_valuesimport'][ self.tos_packet.__dict__['_names'].index(name) ]
        raise AttributeError(name)
    
    def __setattr__(self, name, value):
        if name != 'tos_packet' and name in self.tos_packet.__dict__['_names']:            
            self.tos_packet.__dict__['_values'][ self.tos_packet.__dict__['_names'].index(name) ] = value
        else:
            object.__setattr__(self, name, value)
        

class CTPDebugMsg(TosPacketWrapper):
    AM_ID = 0x72  # 114 in decimal
    
    NET_C_FE_RCV_MSG = 0x21  # This type of message is sent every time a packet is received    
    NET_C_TREE_SENT_BEACON = 0x33  # Indicates that a beacon was sent from the basestation
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
    def __init__(self, packet=None):
        TosPacketWrapper.__init__(self   ,
                                [('type' , 'int', 1),
                                 ('data' , 'blob', None),
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
    formatter = logging.Formatter(datefmt='%H:%M:%S', fmt="%(asctime)s : %(name)-18s: %(levelname)-8s: %(message)s")
    ch.setFormatter(formatter)
    
    fh = logging.FileHandler(filename)
    fh.setLevel(FILE_LOG_LEVEL)
    formatter = logging.Formatter(fmt="%(asctime)s: %(name)-18s: %(levelname)-8s: %(message)s")
    fh.setFormatter(formatter)   
    
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger


def save_reading(timestamp, msg, file):
    global logger 
    global mote_type
    delay = 0
    if msg.delay >= 5000:
        delay = 0
    else:
        delay = msg.delay
    publish_reading(msg)
    voltage = 0
    if mote_type == 'iris':
        voltage = raw_to_volts_iris(msg.readingVoltage)
    elif mote_type == 'micaz':
        voltage = raw_to_volts_micaz(msg.readingVoltage)
    if msg.source % 10 == 0:
        readingTemperature = 0
        msg.readingLight = 0
    else:
        readingTemperature = raw_to_celcius(msg.readingTemperature)
    logger.info("Mote %d:    Temperature: %f    Light: %d    Voltage: %f    Parent: %d    Metric: %d    Delay: %d" % (msg.source, readingTemperature, msg.readingLight, voltage, msg.parent, msg.metric, msg.delay))
    file.write("%f %d %d %f %d %f\n" % (timestamp-delay, msg.source, msg.seqno, readingTemperature, msg.readingLight, voltage))
    file.flush()
            
def publish_reading(msg):
    global mote_type
    if mote_type == 'iris':
        voltage = raw_to_volts_iris(msg.readingVoltage)
    elif mote_type == 'micaz':
        voltage = raw_to_volts_micaz(msg.readingVoltage)
    if msg.source % 10 == 0:
        readingTemperature = 0
        msg.readingLight = 0
    else:
        readingTemperature = raw_to_celcius(msg.readingTemperature)
    try:
        event = '%d %d %f %d %f %d %d' % (msg.source, msg.seqno, readingTemperature, msg.readingLight, voltage, msg.parent, msg.metric)
        publish(ALERT_INFO, (datetime.datetime.now() - datetime.timedelta(milliseconds=msg.delay)), event, EXCHANGE_READINGS)
    except TypeError, e:
        print e        
    
    
def print_ctp_header_info(ctp_packet_header):
    global logger
    logger.info("CTP header informations:: Options: %d    THL: %d    ETX: %d    Origin: %d    OriginSeqNo: %d    CollectionId: %d" % (ctp_packet_header.options, ctp_packet_header.thl, ctp_packet_header.etx, ctp_packet_header.origin, ctp_packet_header.originSeqNo, ctp_packet_header.collectionId))

def new_multihopsensing_packet(data, mote_type):
    msg = None                                   
    if data:
        try:                              
            msg = MultihopSensingMsg(mote_type, data)  # convert a packet
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
        print "Usage: python %s serial@/dev/ttyUSB1:57600 {message_type (e.g. 0xee)} {mote_type (micaz/iris)} [ignore list]" % (args[0])
        sys.exit()    
    global AM_ID       
    AM_ID = int(args[2], 16)
    global mote_type
    mote_type = args[3].strip()
    if not mote_type in RECOGNIZED_MOTES:
        print 'Unrecognized mote "%s"' % mote_type
        exit()
        
    motes_to_ignore = []
    if len(args) >= 5:
        motes_to_ignore = map(int, args[4].split(','))
    
    exp_start = datetime.datetime.now().strftime("%d_%m_%y_%Hh%Mm%Ss")
    file_samples = open("Output/samples_%s.agg" % exp_start, "w")
    logger = create_logger("Output/Log/log_%s.txt" % (exp_start))
    
    '''
    Contains a list of every mote. 
    '''
    motes = set()
    
    try:
        am = tos.AM()
        logger.warning("Starting...")
        
        while True:
            p = am.read()  # get a packet
            if p and p.type == AM_ID:  # it is a MultihopSensing packet                
                now = time.time()
                ctp = CtpData(p.data)
                samples = Samples(ctp.data)
                if samples.source not in motes_to_ignore:
                    if samples.readingTemperature != 0:
                        save_reading(now, samples, file_samples)
                    # print_ctp_header_info(ctp)                  
                    '''
                    Detect new motes as they appear on the network
                    '''
                    last_len = len(motes)
                    motes.add(samples.source)
                    curr_len = len(motes)
                    if last_len < curr_len:
                        logger.warning("Mote %d entered the network!" % samples.source)
            else:
                if p and p.type == CTPDebugMsg.AM_ID:                    
                    msg = CTPDebugMsg(p.data)
                    msg.process()
                else:
                    logger.warning("Skipping packet %s" % p)
    except KeyboardInterrupt:
        # print_database() #to test persistence in to database
        logger.warning("Aborting...")
    except SystemExit:
        pass  # nothing to say about system exit
    except:
        logger.exception("An unhandled exception occurred.")
    finally:
        file_samples.close()
        logger.warning("Done...")


if __name__ == "__main__":
    main(sys.argv)
