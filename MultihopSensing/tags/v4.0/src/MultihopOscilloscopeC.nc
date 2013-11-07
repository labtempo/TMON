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
#include <math.h>
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

		interface Timer<TMilli> as TempTimer;
		interface Timer<TMilli> as BatteryTimer;
		interface Timer<TMilli> as LightTimer;
		interface Read<uint16_t> as Temp;
		interface Read<uint16_t> as Voltage;
		interface Read<uint16_t> as Light;
		interface Leds;
	}
}

implementation {
	task void uartSendTask();
	static void startTempTimer(uint32_t interval);
	static void startBatteryTimer(uint32_t interval);
	static void startLightTimer(uint32_t interval);
	static void fatal_problem(uint8_t f);
	static void report_problem();
	static void report_sent();
	static void report_received();
	static void disseminate(oscilloscope_t msg);
	static float adc_to_celsius(uint16_t adc);
	static float temp_diff(uint16_t adc_a, uint16_t adc_b);

	uint8_t uartlen;
	message_t sendbuf;
	message_t uartbuf;
	bool sendbusy = FALSE, uartbusy = FALSE;

	/* Current local state */
	oscilloscope_t local_oscilloscope;
	oscilloscope_t local_battery_msg;
	oscilloscope_t local_light_msg;
	
	uint16_t last_reading = NULL_TEMP_READING; // temp reading
	uint16_t last_light_reading = 0;
	uint16_t suppressed_temp_msgs = 0;
	
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
		local_light_msg.id = TOS_NODE_ID;
		local_light_msg.type = LIGHT_MSG_TYPE;
		local_light_msg.count = 0;
		
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
				startTempTimer(TEMP_SAMPLE_PERIOD);
				startLightTimer(LIGHT_SAMPLE_PERIOD);
			}
			
			startBatteryTimer(BATTERY_MSG_PERIOD);
		}

		dbg("Temp", "SerialControl done.\n");
	}

	static void startTempTimer(uint32_t interval) {
		if(call TempTimer.isRunning()) 
			call TempTimer.stop();
		call TempTimer.startPeriodic(interval);
		//dbg("Temp", "Start timer.\n");
	}
	
	static void startBatteryTimer(uint32_t interval) {
		if(call BatteryTimer.isRunning()) 
			call BatteryTimer.stop();
		call BatteryTimer.startPeriodic(interval);
		//dbg("Temp", "Start timer.\n");
	}
	
	static void startLightTimer(uint32_t interval) {
		if(call LightTimer.isRunning()) 
			call LightTimer.stop();
		call LightTimer.startPeriodic(interval);
		//dbg("Temp", "Start timer.\n");
	}
	
	static void disseminate(oscilloscope_t msg)
	{
		if(!sendbusy) {
			oscilloscope_t * o = (oscilloscope_t * ) call Send.getPayload(&sendbuf,
					sizeof(oscilloscope_t));
			if(o == NULL) {
				fatal_problem(7);
				return;
			}
			memcpy(o, &msg, sizeof(msg));
			if(call Send.send(&sendbuf, sizeof(msg)) == SUCCESS) {
				sendbusy = TRUE;
			}
			else 
				report_problem();
		}
	}
	
	static float adc_to_celsius(uint16_t adc)
	{   
	    double Rth;
	    double ln_Rth;
	    double TK;
	    
	    if (adc <= 0U)		
        	return -1.0f;    	
	    
	    Rth = 10000 * (1023.0 - adc) / adc;	    
	    if (Rth <= 0.0)
	        return -1.0f;
	        
	    ln_Rth = log(Rth);
	    
	    // temperature in Kelvins
	    TK = 1. / (0.001010024 + 0.000242127 * ln_Rth + 0.000000146 * ln_Rth * ln_Rth * ln_Rth);
	    
	    // temperature in Celsius
	    return (float)(TK - 273.15);
	}
	
	static float temp_diff(uint16_t adc_a, uint16_t adc_b)
	{   
	    /*
	     * This function calculates the difference between two temperatures measured by  the ADC.
	     * 
	     * The calculation is made through a Taylor series approximation of order 5. This means that
	     * a polynomial of order 5: 
	     * P(x) = 36.5995+0.108762*(x-625)+0.0000815986*(x-625)**2+2.1513*10**-7*(x-625)**3+3.4719*10**-10*(x-625)**4+
	     * 8.23509*10**-13*(x-625)**5 is used in place of the real calculation (see adc_to_celsius).
	     * 
	     * The approximated Taylor series is centered at point 625, ~26 degrees C. This is the mean
	     * of the interval [350,900], which corresponds to the range of [10 C, 72 C].
	     * 
	     * Compared to adc_to_celsius, this function uses only: 13 multiplications and 10 additions/subtractions,
	     * considering that most math is over integers.
	     * While adc_to_celsius uses: 1 function call (log), 2 divisions, 5 multiplications, 
	     * 4 additions/subtractions.
	     */
	    
	    int16_t adc_diff1_a = adc_a - 625;
	    int16_t adc_diff2_a = adc_diff1_a * adc_diff1_a;
	    int16_t adc_diff3_a = adc_diff2_a * adc_diff1_a;
	    int16_t adc_diff4_a = adc_diff3_a * adc_diff1_a;
	    int16_t adc_diff5_a = adc_diff4_a * adc_diff1_a;
	    int16_t adc_diff1_b = adc_b - 625;
	    int16_t adc_diff2_b = adc_diff1_b * adc_diff1_b;
	    int16_t adc_diff3_b = adc_diff2_b * adc_diff1_b;
	    int16_t adc_diff4_b = adc_diff3_b * adc_diff1_b;
	    int16_t adc_diff5_b = adc_diff4_b * adc_diff1_b;	    
	    		
		float t = (float)( 0.108762 * (adc_diff1_a - adc_diff1_b) +  0.0000815986 * (adc_diff2_a - adc_diff2_b) \
				           + 2.1513e-07 * (adc_diff3_a - adc_diff3_b) + 3.4719e-10 * (adc_diff4_a - adc_diff4_b) \
				           + 8.23509e-13 * (adc_diff5_a - adc_diff5_b) ); 
		
	    return t < 0.0 ? -t : t;
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
		float t_diff = 0.0f;
						
		if(call Temp.read() != SUCCESS)
			fatal_problem(7);		
		
		if (last_reading != NULL_TEMP_READING && local_oscilloscope.reading != NULL_TEMP_READING)
		{					
			t_diff = temp_diff(last_reading, local_oscilloscope.reading);			
			dbg("Temp", "Everything is ok, temp diff is: %f\n", t_diff);	
		}
		else if (local_oscilloscope.reading == NULL_TEMP_READING) // assure that will not send if the current_temp is messed up
		{
			suppressed_temp_msgs = suppressed_temp_msgs == MAX_TEMP_SUPPRESSION_MSGS ? suppressed_temp_msgs - 1: suppressed_temp_msgs;
			dbg("Temp", "Curr temp is messed up: %d\n", local_oscilloscope.reading);
		}
		else // (last_reading <= 0) make sure that will send regardless of temp_diff 
		{
			suppressed_temp_msgs = MAX_TEMP_SUPPRESSION_MSGS;
			dbg("Temp", "Last temp is messed up: %f\n", last_reading);
		}
		
		if(t_diff >= TEMPERATURE_DELTA || suppressed_temp_msgs == MAX_TEMP_SUPPRESSION_MSGS) {			
			dbg("Temp", "Sending temp reading: %d. Temp diff is: %f\n", local_oscilloscope.reading, t_diff);

			atomic {
				disseminate(local_oscilloscope);
			}
			suppressed_temp_msgs = 0;
			last_reading = local_oscilloscope.reading;
			if (local_oscilloscope.count == MAX_COUNT)
				local_oscilloscope.count = 0;
			else
				local_oscilloscope.count++;
		}
		else
		{
			suppressed_temp_msgs++;
		}	
	}
	
	
	event void BatteryTimer.fired() {		
		if (call Voltage.read() != SUCCESS) 
			fatal_problem(7);
		
		dbg("Temp", "Sending battery reading: %d\n", local_battery_msg.reading);
		
		atomic {
			disseminate(local_battery_msg);
		}
		
		if (local_battery_msg.count == MAX_COUNT)
			local_battery_msg.count = 0;
		else
			local_battery_msg.count++;			
	}
	
	
	event void LightTimer.fired() {
		int16_t diff;
		
		if (call Light.read() != SUCCESS) 
			fatal_problem(7);
		
		diff = last_light_reading - local_light_msg.reading;
		diff = diff < 0 ? -diff : diff;
		
		if (diff > LIGHT_DIFF_THRESHOLD) 
		{
			dbg("Temp", "Sending light reading: %d\n", local_light_msg.reading);
			
			atomic {
				disseminate(local_light_msg);
			}
			
			if (local_light_msg.count == MAX_COUNT)
				local_light_msg.count = 0;
			else
				local_light_msg.count++;
			
			last_light_reading = local_light_msg.reading;
		}			
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
			data = NULL_TEMP_READING;
			report_problem();
		}		
		local_oscilloscope.reading = (data < MAX_TEMP_READING && data > MIN_TEMP_READING) ? data : NULL_TEMP_READING;
		//dbg("Temp", "Read sensor: %d.\n", data);
	}
	
	event void Voltage.readDone(error_t result, uint16_t data) {
		if(result != SUCCESS) {
			data = 0xffff;
			fatal_problem(5);
		}
		local_battery_msg.reading = data;
	}
	
	event void Light.readDone(error_t result, uint16_t data) {
		if(result != SUCCESS) {
			data = 0xffff;
			fatal_problem(5);
		}
		local_light_msg.reading = data;
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