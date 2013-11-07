/*
 * Copyright (c) 2006 Intel Corporation
 * All rights reserved.
 *
 * This file is distributed under the terms in the attached INTEL-LICENSE     
 * file. If you do not find these files, copies can be found by writing to
 * Intel Research Berkeley, 2150 Shattuck Avenue, Suite 1300, Berkeley, CA, 
 * 94704.  Attention:  Intel License Inquiry.
 */

/**
 * @author David Gay
 * @author Kyle Jamieson
 */

#ifndef MULTIHOP_OSCILLOSCOPE_H
#define MULTIHOP_OSCILLOSCOPE_H

enum {
  AM_OSCILLOSCOPE = 0x95,  
  OSCILLOSCOPE_MSG_TYPE = 0,
  BATTERY_MSG_TYPE = 1,
  ROUTER_NODE_DIVIDER = 10,
  BASE_STATION_ID = 255,
  MIN_INTERVAL = 1000,
  MAX_INTERVAL = 10000,
  MAX_COUNT = 65535U, //(2^16) - 1,
  BATTERY_MSG_PERIOD = (10 * 60 * 1000),
};

typedef nx_struct oscilloscope {
	nx_uint16_t id;
	/* Mote id of sending mote. */
	nx_uint16_t count;
	/* The readings are samples count * NREADINGS onwards */
	nx_uint16_t reading;
	nx_uint8_t type;
} oscilloscope_t;

#endif
