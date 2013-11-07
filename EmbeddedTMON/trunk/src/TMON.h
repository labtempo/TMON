#ifndef TEST_NETWORK_H
#define TEST_NETWORK_H

#include <AM.h>

enum {
 AM_TESTNETWORKMSG = 0x05,
 SAMPLE_RATE_KEY = 0x1,
 SAMPLES = 0xee,
 TEST_NETWORK_QUEUE_SIZE = 8,
 SAMPLE_INTERVAL =  1*1024U, //1 second
 NULL_TEMP_READING = 0, // indicates failure or out of range reading
 MAX_SUPPRESSION_MSGS = 300,//Max messages suppressed
 NUMBER_INITIAL_MSGS = 30,// Number of messages send in initial phase o program
 INITIAL_MAX_SUPPRESSION_MSGS = 60,// Max messages suppressed in initial phase o program
 LIGHT_DIFF_THRESHOLD = 200, // min difference that will trigger a send  
};

#define TEMPERATURE_DELTA 0.5 // min temperature difference that will trigger a send

typedef nx_struct TMON {
  nx_uint16_t readingTemperature; /* Reading of temperature */
  nx_uint16_t readingLight; /* Reading of light */
  nx_uint16_t readingVoltage; /* Reading of Voltage */
  /*
   * variables to get informations about WSN
   */
  nx_am_addr_t source; /* Source address of sending mote. */
  nx_uint16_t seqno;  /* Sequence number of the send*/
  nx_am_addr_t parent; /* Parent of sending mote. */
  nx_uint16_t metric; /* ETX cost of transmission*/
  nx_uint32_t delay; /* Delay of data collection */  
} TMON_t;

#endif
