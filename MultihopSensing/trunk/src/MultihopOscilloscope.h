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
  LIGHT_MSG_TYPE = 2,
  ROUTER_NODE_DIVIDER = 10,
  BASE_STATION_ID = 255,
  TEMP_SAMPLE_PERIOD = 10240, // 10 second
  MAX_TEMP_SUPPRESSION_MSGS = 60,   
  MAX_COUNT = 65535U, // (2^16) - 1,
  BATTERY_MSG_PERIOD = 3686400U, // 60min
  LIGHT_SAMPLE_PERIOD = 10240, // 10 seconds
  NULL_TEMP_READING = 0, // indicates failure or out of range reading
  MAX_TEMP_READING = 900,
  MIN_TEMP_READING = 350,
  LIGHT_DIFF_THRESHOLD = 200, // min difference that will trigger a send
  MAX_INITIAL_BATTERY_MSGS = 5,
  LEAVES_RADIO_SLEEP_TIME = 00005, //percentage * 100 of radio work
};

#define TEMPERATURE_DELTA 0.5 // min temperature difference that will trigger a send

typedef nx_struct oscilloscope {
	nx_uint16_t id;
	/* Mote id of sending mote. */
	nx_uint16_t count;
	/* The readings are samples count * NREADINGS onwards */
	nx_uint16_t reading;
	nx_uint8_t type;
} oscilloscope_t;

#endif
