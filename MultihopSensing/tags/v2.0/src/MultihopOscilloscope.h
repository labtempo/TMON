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
  /* Number of readings per message. If you increase this, you may have to
     increase the message_t size. */
  NREADINGS = 5,
  /* Default sampling period. */
  AM_OSCILLOSCOPE = 0x95,
  ROUTER_NODE_DIVIDER = 10,
  BASE_STATION_ID = 255,
  MIN_INTERVAL = 1000,
  MAX_INTERVAL = 10000,
};

typedef nx_struct oscilloscope {
  //nx_uint16_t version; /* Version of the interval. */
  //nx_uint16_t interval; /* Sampling period. */
  nx_uint16_t id; /* Mote id of sending mote. */
  nx_uint16_t count; /* The readings are samples count * NREADINGS onwards */
  nx_uint16_t reading;
} oscilloscope_t;

#endif
