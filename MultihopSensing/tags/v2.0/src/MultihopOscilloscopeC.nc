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
 * MultihopOscilloscope demo application using the collection layer. 
 * See README.txt file in this directory and TEP 119: Collection.
 *
 * @author David Gay
 * @author Kyle Jamieson
 */ 

#include "Timer.h"
#include "MultihopOscilloscope.h"

module MultihopOscilloscopeC @safe() {
	uses {
		// Interfaces for initialization:
		interface Boot;
		interface SplitControl as RadioControl;
		interface SplitControl as SerialControl;
		interface StdControl as RoutingControl;

		// Interfaces for communication, multihop and serial:
		interface Send;
		interface Receive as Snoop;
		interface Receive;
		interface AMSend as SerialSend;
		interface CollectionPacket;
		interface RootControl;

		interface Queue<message_t *> as UARTQueue;
		interface Pool<message_t> as UARTMessagePool;

		// Miscalleny:
		interface Timer<TMilli>;
		interface Read<uint16_t>;
		interface Leds;
	}
}

implementation {
	task void uartSendTask();
	static void startTimer(int16_t interval);
	static void fatal_problem(unsigned short f);
	static void report_problem();
	static void report_sent();
	static void report_received();

	uint8_t uartlen;
	message_t sendbuf;
	message_t uartbuf;
	bool sendbusy = FALSE, uartbusy = FALSE;

	/* Current local state - interval, version and accumulated readings */
	oscilloscope_t local;
	
	uint16_t last_reading = 0;
	
	int16_t curr_interval = MIN_INTERVAL;

	/* When we head an Oscilloscope message, we check it's sample count. If
	 it's ahead of ours, we "jump" forwards (set our count to the received
	 count). However, we must then suppress our next count increment. This
	 is a very simple form of "time" synchronization (for an abstract
	 notion of time). */
	bool suppress_count_change;

	// 
	// On bootup, initialize radio and serial communications, and our
	// own state variables.
	//
	event void Boot.booted() {		
		local.id = TOS_NODE_ID;		
		
		// Beginning our initialization phases:
		if(call RadioControl.start() != SUCCESS) 
			fatal_problem(7);

		if(call RoutingControl.start() != SUCCESS) 
			fatal_problem(7);

		dbg("Boot", "Booted with ID = %d.\n", TOS_NODE_ID);
	}

	event void RadioControl.startDone(error_t error) {
		if(error != SUCCESS) 
			fatal_problem(7);

		if(sizeof(local) > call Send.maxPayloadLength()) 
			fatal_problem(7);

		if(call SerialControl.start() != SUCCESS) 
			fatal_problem(5);
		dbg("Temp", "RadioControl start done.\n");
	}

	event void SerialControl.startDone(error_t error) {
		if(error != SUCCESS) 
			fatal_problem(7);

		// This is how to set yourself as a root to the collection layer:
		if(local.id == BASE_STATION_ID) {
			call RootControl.setRoot();
			dbg("Temp", "I'm now root.\n");
		}
		else
		{
			// REMOVE THIS: || local.id == 10
			if (local.id % ROUTER_NODE_DIVIDER != 0)
			{
				/*
				 * Will not start reading samples of base station or
				 * router nodes.
				 */
				startTimer(curr_interval);
			}
		}

		dbg("Temp", "SerialControl done.\n");
	}

	static void startTimer(int16_t interval) {
		if(call Timer.isRunning()) 
			call Timer.stop();
		call Timer.startPeriodic(interval);
		//dbg("Temp", "Start timer.\n");
	}

	event void RadioControl.stopDone(error_t error) {
	}
	event void SerialControl.stopDone(error_t error) {		
	}

	//
	// Only the root will receive messages from this interface; its job
	// is to forward them to the serial uart for processing on the pc
	// connected to the sensor network.
	//
	event message_t * Receive.receive(message_t * msg, void * payload,
			uint8_t len) {
		oscilloscope_t * in = (oscilloscope_t *) payload;
		oscilloscope_t * out;
		
		dbg("Radio",
				"Sample [count = %d] received from %d.\n", in->count, in->id);

		if(uartbusy == FALSE) {
			out = (oscilloscope_t * ) call SerialSend.getPayload(&uartbuf,
					sizeof(oscilloscope_t));
			if(len != sizeof(oscilloscope_t) || out == NULL) {				
				return msg;
			}
			else {
				memcpy(out, in, sizeof(oscilloscope_t));
			}
			uartlen = sizeof(oscilloscope_t);
			post uartSendTask();
		}
		else {
			// The UART is busy; queue up messages and service them when the
			// UART becomes free.		
			message_t * newmsg = call UARTMessagePool.get();
			if(newmsg == NULL) {
				// drop the message on the floor if we run out of queue space.
				report_problem();
				return msg;
			}

			//Serial port busy, so enqueue.
			out = (oscilloscope_t * ) call SerialSend.getPayload(newmsg,
					sizeof(oscilloscope_t));
			if(out == NULL) {
				return msg;
			}
			memcpy(out, in, sizeof(oscilloscope_t));

			if(call UARTQueue.enqueue(newmsg) != SUCCESS) {
				// drop the message on the floor and hang if we run out of
				// queue space without running out of queue space first (this
				// should not occur).
				dbg("Radio", "Sample queue is full.\n");
				call UARTMessagePool.put(newmsg);
				fatal_problem(7);
				return msg;
			}
			else 
				dbg("Radio", "Sample enqueued.\n");
		}

		return msg;
	}

	task void uartSendTask() {
		oscilloscope_t * out;
		out = (oscilloscope_t * ) call SerialSend.getPayload(&uartbuf,
				sizeof(oscilloscope_t));
		//dbg("Temp", "Uart send task: id=%d, counter=%d\n", out->id, out->count);
		if(call SerialSend.send(0xffff, &uartbuf, uartlen) != SUCCESS) {
			report_problem();
		}
		else {
			uartbusy = TRUE;
		}
	}

	event void SerialSend.sendDone(message_t * msg, error_t error) {
		uartbusy = FALSE;
		if(call UARTQueue.empty() == FALSE) {
			// We just finished a UART send, and the uart queue is
			// non-empty.  Let's start a new one.
			message_t * queuemsg = call UARTQueue.dequeue();
			if(queuemsg == NULL) {
				fatal_problem(7);
				return;
			}
			memcpy(&uartbuf, queuemsg, sizeof(message_t));
			if(call UARTMessagePool.put(queuemsg) != SUCCESS) {
				fatal_problem(7);
				return;
			}			
			post uartSendTask();
		}
		call Leds.led1Toggle();
		dbg("Temp", "Sent to serial.\n");		
	}

	//
	// Overhearing other traffic in the network.
	//
	event message_t * Snoop.receive(message_t * msg, void * payload,
			uint8_t len) {
		oscilloscope_t * omsg = payload;
		
		if (local.id % ROUTER_NODE_DIVIDER != 0 && local.id != BASE_STATION_ID && local.id != omsg->id)
		{
			dbg("Radio", "Overheard traffic from %d.\n", omsg->id);
	
			report_received();
	
			// If we hear from a future count, jump ahead but suppress our own
			// change.
			if(omsg->count > local.count) {
				dbg("Radio", "Updating count.\n");
				local.count = omsg->count;
				suppress_count_change = TRUE;
			}		
		}
		return msg;
	}

	/* At each sample period:
	 - if local sample buffer is full, send accumulated samples
	 - read next sample
	 */
	event void Timer.fired() {
		//dbg("Temp", "Starting sensor sampling.\n");
		if(local.reading != last_reading || curr_interval == MAX_INTERVAL) {			
			dbg("Temp", "Sending reading. %d %d\n", local.reading, last_reading);

			if(!sendbusy) {
				oscilloscope_t * o = (oscilloscope_t * ) call Send.getPayload(&sendbuf,
						sizeof(oscilloscope_t));
				if(o == NULL) {
					fatal_problem(7);
					return;
				}
				memcpy(o, &local, sizeof(local));
				if(call Send.send(&sendbuf, sizeof(local)) == SUCCESS) {
					sendbusy = TRUE;
				}
				else 
					report_problem();
			}

			/* Part 2 of cheap "time sync": increment our count if we didn't
			 jump ahead. */
			if(!suppress_count_change)
			{ 
				local.count++;
			}
			suppress_count_change = FALSE;
			
			curr_interval = curr_interval - 1000;
			
			if (curr_interval < MIN_INTERVAL)
				curr_interval = MIN_INTERVAL;			
		}
		else
		{			
			curr_interval = curr_interval + 1000;
			dbg("Temp", "Increasing interval %d.\n", curr_interval);
			
			if (curr_interval > MAX_INTERVAL)
				curr_interval = MAX_INTERVAL;
		}

		if(call Read.read() != SUCCESS) 
			fatal_problem(7);
			
		startTimer(curr_interval);
	}

	event void Send.sendDone(message_t * msg, error_t error) {
		if(error == SUCCESS) 
			report_sent();
		else 
			report_problem();

		sendbusy = FALSE;
	}

	event void Read.readDone(error_t result, uint16_t data) {
		if(result != SUCCESS) {
			data = 0xffff;
			report_problem();
		}
		last_reading = local.reading;
		local.reading = data;
		//dbg("Temp", "Read sensor: %d.\n", data);
	}

	// Use LEDs to report various status issues.
	static void fatal_problem(unsigned short f) {
		if (f & 0x01)		
			call Leds.led0On();
		else
			call Leds.led0Off();
		if (f & 0x02)		
			call Leds.led1On();
		else
			call Leds.led1Off();			
		if (f & 0x03)		
			call Leds.led2On();
		else
			call Leds.led2Off();
		call Timer.stop();
		dbgerror("Error", "Fatal error.\n");
	}

	static void report_problem() {
		call Leds.led0Toggle();
	}
	static void report_sent() {
		call Leds.led1Toggle();
		dbg("Radio", "Message sent.\n");
	}
	static void report_received() {
		call Leds.led2Toggle();
		dbg("Radio", "Message received.\n");
	}
}