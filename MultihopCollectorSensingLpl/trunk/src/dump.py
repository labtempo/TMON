#!/usr/bin/env python

import sys, time
import tos

class Samples(tos.Packet):
    def __init__(self, payload = None):
        tos.Packet.__init__(self,
                               [('id',   'int', 2),
                                ('sendCount',    'int', 2),
                                ('readingTemperature',   'int', 2),
                                ('readingLight',   'int', 2),
                                ('readingVoltage', 'int', 2)],
                                payload)
        
class CtpData(tos.Packet):
    def __init__(self, payload = None):
        tos.Packet.__init__(self,
                               [('options',     'int', 1),
                                ('thl',         'int', 1),
                                ('etx',         'int', 2),
                                ('origin',      'int', 2),
                                ('originSeqNo', 'int', 1),
                                ('collectionId','int', 1),
                                ('data',  'blob', None)],
                               payload)

if len(sys.argv) < 2:
    print "Usage:", sys.argv[0], "serial@/dev/ttyUSB1:57600"
    sys.exit()

#s = tos.Serial(sys.argv[1], int(sys.argv[2]), debug=False)
am = tos.AM()

while True:
    p = am.read()
    if p:
        if p.type == 238:
            ts = "%.4f" % time.time()
            ctp = CtpData(p.data)
            samples = Samples(ctp.data)
            print ts, '\t', ctp
            print ts, '\t', samples
        else:
            print p

