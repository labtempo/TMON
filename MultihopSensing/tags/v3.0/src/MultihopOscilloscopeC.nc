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
		interface Receive;
		interface Receive as Snoop;
		interface AMSend as SerialSend;
		interface CollectionPacket;
		interface RootControl;

		interface Queue<message_t *> as UARTQueue;
		interface Pool<message_t> as UARTMessagePool;

		// Miscalleny:
		interface Timer<TMilli> as TempTimer;
		interface Timer<TMilli> as BatteryTimer;
		interface Read<uint16_t> as Temp;
		interface Read<uint16_t> as Voltage;
		interface Leds;
	}
}

implementation {
	task void uartSendTask();
	static void startTempTimer(int16_t interval);
	static void startBatteryTimer(int16_t interval);
	static void fatal_problem(uint8_t f);
	static void report_problem();
	static void report_sent();
	static void report_received();

	uint8_t uartlen;
	message_t sendbuf;
	message_t uartbuf;
	bool sendbusy = FALSE, uartbusy = FALSE;

	/* Current local state */
	oscilloscope_t local_oscilloscope;
	oscilloscope_t local_battery_msg;
	
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
		local_oscilloscope.id = TOS_NODE_ID;
		local_oscilloscope.type = OSCILLOSCOPE_MSG_TYPE;
		local_oscilloscope.count = 0;
		local_battery_msg.id = TOS_NODE_ID;
		local_battery_msg.type = BATTERY_MSG_TYPE;
		local_battery_msg.count = 0;
		
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

		if(sizeof(local_oscilloscope) > call Send.maxPayloadLength()) 
			fatal_problem(7);

		if(call SerialControl.start() != SUCCESS) 
			fatal_problem(5);
		dbg("Temp", "RadioControl start done.\n");
	}

	event void SerialControl.startDone(error_t error) {
		if(error != SUCCESS) 
			fatal_problem(7);

		// This is how to set yourself as a root to the collection layer:
		if(local_oscilloscope.id == BASE_STATION_ID) {
			call RootControl.setRoot();
			dbg("Temp", "I'm now root.\n");
		}
		else
		{
			if (local_oscilloscope.id % ROUTER_NODE_DIVIDER != 0)
			{
				/*
				 * Will not start reading samples of base station or
				 * router nodes.
				 */
				startTempTimer(curr_interval);
			}
			
			startBatteryTimer(BATTERY_MSG_PERIOD);
		}

		dbg("Temp", "SerialControl done.\n");
	}

	static void startTempTimer(int16_t interval) {
		if(call TempTimer.isRunning()) 
			call TempTimer.stop();
		call TempTimer.startOneShot(interval);
		//dbg("Temp", "Start timer.\n");
	}
	
	static void startBatteryTimer(int16_t interval) {
		if(call BatteryTimer.isRunning()) 
			call BatteryTimer.stop();
		call BatteryTimer.startPeriodic(interval);
		//dbg("Temp", "Start timer.\n");
	}

	event void RadioControl.stopDone(error_t error) {
	}
	event void SerialControl.stopDone(error_t error) {		
	}

		//
	// Overhearing other traffic in the network.
	//
	event message_t * Snoop.receive(message_t * msg, void * payload,
			uint8_t len) {		
		return msg;
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
				"Sample [count = %d, type = %d] received from %d.\n", in->count, in->type, in->id);

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


	event void TempTimer.fired() {
		//dbg("Temp", "Starting sensor sampling.\n");
		if(local_oscilloscope.reading != last_reading || curr_interval == MAX_INTERVAL) {			
			dbg("Temp", "Sending temp reading: %d\n", local_oscilloscope.reading);

			if(!sendbusy) {
				oscilloscope_t * o = (oscilloscope_t * ) call Send.getPayload(&sendbuf,
						sizeof(oscilloscope_t));
				if(o == NULL) {
					fatal_problem(7);
					return;
				}
				memcpy(o, &local_oscilloscope, sizeof(local_oscilloscope));
				if(call Send.send(&sendbuf, sizeof(local_oscilloscope)) == SUCCESS) {
					sendbusy = TRUE;
				}
				else 
					report_problem();
			}

			/* Part 2 of cheap "time sync": increment our count if we didn't
			 jump ahead. */
			if(!suppress_count_change)
			{ 
				if (local_oscilloscope.count == MAX_COUNT)
					local_oscilloscope.count = 0;
				else
					local_oscilloscope.count++;
			}
			suppress_count_change = FALSE;
			
			curr_interval = curr_interval - 1000;
			
			if (curr_interval < MIN_INTERVAL)
				curr_interval = MIN_INTERVAL;			
		}
		else
		{			
			curr_interval = curr_interval + 1000;
			dbg("Temp", "Increasing interval: %d.\n", curr_interval);
			
			if (curr_interval > MAX_INTERVAL)
				curr_interval = MAX_INTERVAL;
		}

		if(call Temp.read() != SUCCESS) 
			fatal_problem(7);
			
		startTempTimer(curr_interval);
	}
	
	
	event void BatteryTimer.fired() {
		//dbg("Temp", "Starting sensor sampling.\n");					
			dbg("Temp", "Sending battery reading: %d\n", local_battery_msg.reading);

		if(!sendbusy) {
			oscilloscope_t * o = (oscilloscope_t * ) call Send.getPayload(&sendbuf,
					sizeof(oscilloscope_t));
			if(o == NULL) {
				fatal_problem(7);
				return;
			}
			memcpy(o, &local_battery_msg, sizeof(local_battery_msg));
			if(call Send.send(&sendbuf, sizeof(local_battery_msg)) == SUCCESS) {
				sendbusy = TRUE;
			}
			else 
				report_problem();
		}
		
		if (local_battery_msg.count == MAX_COUNT)
			local_battery_msg.count = 0;
		else
			local_battery_msg.count++;
		
		if (call Voltage.read() != SUCCESS) 
			fatal_problem(7);			
	}
	
	// CollectionSenderC
	event void Send.sendDone(message_t * msg, error_t error) {
		if(error == SUCCESS) 
			report_sent();
		else 
			report_problem();

		sendbusy = FALSE;
	}

	event void Temp.readDone(error_t result, uint16_t data) {
		if(result != SUCCESS) {
			data = 0xffff;
			report_problem();
		}
		last_reading = local_oscilloscope.reading;
		local_oscilloscope.reading = data;
		//dbg("Temp", "Read sensor: %d.\n", data);
	}
	
	event void Voltage.readDone(error_t result, uint16_t data) {
		if(result != SUCCESS) {
			data = 0xffff;
			fatal_problem(5);
		}
		local_battery_msg.reading = data;
	}

	// Use LEDs to report various status issues.
	static void fatal_problem(uint8_t f) {		
		call Leds.set(f);		
		call TempTimer.stop();
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