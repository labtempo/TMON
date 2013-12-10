/**
 * @author Philip Levis
 * @author Gustavo Zanatta Bruno
 * @version $Revision: 1.1 $ $Date: 2009-09-16 00:53:47 $
 */

#include <Timer.h>
#include "TestNetwork.h"
#include "CtpDebugMsg.h"

module MCSLC {
	uses interface Boot;
	uses interface SplitControl as RadioControl;
	uses interface SplitControl as SerialControl;
	uses interface StdControl as RoutingControl;
	uses interface StdControl as DisseminationControl;
	uses interface DisseminationValue<uint32_t> as DisseminationPeriod;
	uses interface Send;
	uses interface Leds;
	uses interface Read<uint16_t> as Temp;
	uses interface Read<uint16_t> as Light;	
	uses interface Read<uint16_t> as Volt;	
	uses interface Timer<TMilli>;
	uses interface RootControl;
	uses interface Receive;
	uses interface AMSend as UARTSend;
	uses interface CollectionPacket;
	uses interface CtpInfo;
	uses interface CtpCongestion;
	uses interface Random;
	uses interface Queue<message_t*>;
	uses interface Pool<message_t>;
	uses interface CollectionDebug;
	uses interface AMPacket;
	uses interface Packet as RadioPacket;
	uses interface LowPowerListening;
}

implementation {
	static void report_problem_0();
	static void report_problem_1();
	static void report_problem_2();
	static void report_sent();
	static void report_received();
	static void startTimer(uint32_t interval);
	static float adc_to_celsius(uint16_t adc);
	void sendMessage();
	void failedSend();
	
	task void uartEchoTask();
	
	message_t packet;
	message_t uartpacket;
	message_t* recvPtr = &uartpacket;
	uint8_t msglen;
	bool sendBusy = FALSE;
	bool uartbusy = FALSE;
	bool firstTimer = TRUE;
	uint16_t seqno;
	
	uint16_t etxNow = 0;	
	uint16_t temperatureNow = 0;
	uint16_t lightNow = 0;
	uint16_t voltageNow = 0;
	uint16_t lastEtx = 0;
	uint16_t lastTemperature = 0;
	uint16_t lastLight = 0;
	uint16_t suppressedTemperatures = 0;
		
	
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
		
	event void Boot.booted() {
		call SerialControl.start();
		dbg("Boot", "Booted with ID = %d.\n", TOS_NODE_ID);
	}

	event void SerialControl.startDone(error_t err) {
		if (TOS_NODE_ID % 500 == 0) {
			call LowPowerListening.setLocalWakeupInterval(0);
		}
		call RadioControl.start();
	}

	event void RadioControl.startDone(error_t err) {
		if (err != SUCCESS) {
			call RadioControl.start();
		}
		else {
			//call DisseminationControl.start();
			call RoutingControl.start();
			if (TOS_NODE_ID % 500 == 0) {
				call RootControl.setRoot();
			}else
			{
				startTimer(SAMPLE_INTERVAL);						
				/*
				 * Will not start reading samples of base station
				 */
			}
		}
	}

	static void startTimer(uint32_t interval) {
		if(call Timer.isRunning()) 
			call Timer.stop();
		call Timer.startPeriodic(interval);
		dbg("Sample", "Start timer.\n");
	}

	event void RadioControl.stopDone(error_t err) {}
	event void SerialControl.stopDone(error_t err) {}
		
	event void Timer.fired() {
		float tempDiff = 0.0f;
		int16_t lightDiff;
		dbg("Master", "Timer sample fired.\n");
		//Temperature verification for send
		call Temp.read();		
		if (lastTemperature != NULL_TEMP_READING && temperatureNow != NULL_TEMP_READING)
		{					
			tempDiff = abs(adc_to_celsius(lastTemperature) - adc_to_celsius(temperatureNow))
			dbg("Temp", "Everything is ok, temp diff is: %f\n", tempDiff);	
		}else if (temperatureNow == NULL_TEMP_READING) // assure that will not send if the current_temp is messed up
		{
			suppressedTemperatures = suppressedTemperatures == MAX_SUPPRESSION_MSGS ? suppressedTemperatures - 1: suppressedTemperatures;
		}else // (last_reading <= 0) make sure that will send regardless of tempDifference 
		{
			suppressedTemperatures = MAX_SUPPRESSION_MSGS;
			dbg("Temp", "Last temp is messed up: %f\n", last_reading);
		}
		//Light verification for send
		call Light.read();		
		lightDiff = lastLight - lightNow;
		lightDiff = lightDiff < 0 ? -lightDiff : lightDiff;
		//Voltage verification for send and notification
		call Volt.read();
		if (voltageNow > 624) {
			call Leds.led2Toggle();					
		}
		
		call CtpInfo.getEtx(&etxNow);
		
		if((tempDiff > TEMPERATURE_DELTA) | (suppressedTemperatures == MAX_SUPPRESSION_MSGS) | (lightDiff > LIGHT_DIFF_THRESHOLD) | (lastEtx != etxNow) ) {			
			dbg("MAster", "Sending a reading: %d. Temp diff is: %f\n", temperatureNow, tempDiff);
			atomic{
				if (!sendBusy)
					sendMessage();
			}
			suppressedTemperatures = 0;
			lastTemperature = temperatureNow;
			lastLight = lightNow;
			lastEtx = etxNow;
		}else
		{
			suppressedTemperatures++;
		}
	}

	void sendMessage() {
		am_addr_t parent = 0;
		MCSL_t*								
		msg = (MCSL_t*)call Send.getPayload(&packet, sizeof(MCSL_t));

		msg->readingTemperature = temperatureNow;
		msg->readingLight = lightNow;
		msg->readingVoltage = voltageNow;
		
		
		call CtpInfo.getParent(&parent);
		msg->source = TOS_NODE_ID;
		msg->seqno = seqno;
		msg->parent = parent;
		msg->metric = etxNow;

		if (call Send.send(&packet, sizeof(MCSL_t)) != SUCCESS) {
			failedSend();
			dbg("MCSLC", "%s: Transmission failed.\n", __FUNCTION__);
		}
		else {
			sendBusy = TRUE;
			seqno++;
			dbg("MCSLC", "%s: Transmission succeeded.\n", __FUNCTION__);
		}
	}

	void failedSend() {
		dbg("App", "%s: Send failed.\n", __FUNCTION__);
		call CollectionDebug.logEvent(NET_C_DBG_1);
		call Leds.led0On();		
	}
	
	event void Send.sendDone(message_t* m, error_t err) {
		if (err != SUCCESS) {
			//      call Leds.led0On();
		}
		sendBusy = FALSE;
		dbg("TestNetworkC", "Send completed.\n");
	}

	event void DisseminationPeriod.changed() {
		const uint32_t* newVal = call DisseminationPeriod.get();
		call Timer.stop();
		call Timer.startPeriodic(*newVal);
	}

	event message_t* 
	Receive.receive(message_t* msg, void* payload, uint8_t len) {
		dbg("TestNetworkC", "Received packet at %s from node %hhu.\n", sim_time_string(), call CollectionPacket.getOrigin(msg));
		call Leds.led1Toggle();    
		if (!call Pool.size() <= (TEST_NETWORK_QUEUE_SIZE < 4)? 1:3)  {
			//      call CtpCongestion.setClientCongested(TRUE);
		}
		if (!call Pool.empty() && call Queue.size() < call Queue.maxSize()) {
			message_t* tmp = call Pool.get();
			call Queue.enqueue(msg);
			if (!uartbusy) {
				post uartEchoTask();
			}
			return tmp;
		}
		return msg;
	}

	task void uartEchoTask() {
		dbg("Traffic", "Sending packet to UART.\n");
		if (call Queue.empty()) {
			return;
		}
		else if (!uartbusy) {
			message_t* msg = call Queue.dequeue();
			dbg("Traffic", "Sending packet to UART.\n");
			if (call UARTSend.send(0xffff, msg, call RadioPacket.payloadLength(msg)) == SUCCESS) {
				uartbusy = TRUE;
			}
			else {
				call CollectionDebug.logEventMsg(NET_C_DBG_2,
						call CollectionPacket.getSequenceNumber(msg),
						call CollectionPacket.getOrigin(msg),
						call AMPacket.destination(msg));
			}
		}
	}

	event void Temp.readDone(error_t result, uint16_t data) {
		if (result != SUCCESS) {
			data = 0xffff;
			report_problem_0();
		}
		temperatureNow = data;		
	}

	event void Light.readDone(error_t result, uint16_t data) {
		if (result != SUCCESS) {
			data = 0xffff;
			report_problem_1();
		}
		lightNow = data;
	}

	event void Volt.readDone(error_t result, uint16_t data) {
		if (result != SUCCESS) {
			data = 0xffff;
			report_problem_2();
		}
		voltageNow = data;
	}
	
	event void UARTSend.sendDone(message_t *msg, error_t error) {
		dbg("Traffic", "UART send done.\n");
		uartbusy = FALSE;
		call Pool.put(msg);
		if (!call Queue.empty()) {
			post uartEchoTask();
		} 
		else {
			//        call CtpCongestion.setClientCongested(FALSE);
		}
	}

	/* Default implementations for CollectionDebug calls.
	 * These allow CollectionDebug not to be wired to anything if debugging
	 * is not desired. */
	default command error_t CollectionDebug.logEvent(uint8_t type) {
		return SUCCESS;
	}

	default command error_t CollectionDebug.logEventSimple(uint8_t type, uint16_t arg) {
		return SUCCESS;
	}

	default command error_t CollectionDebug.logEventDbg(uint8_t type, uint16_t arg1, uint16_t arg2, uint16_t arg3) {
		return SUCCESS;
	}
	default command error_t CollectionDebug.logEventMsg(uint8_t type, uint16_t msg, am_addr_t origin, am_addr_t node) {
		return SUCCESS;
	}
	default command error_t CollectionDebug.logEventRoute(uint8_t type, am_addr_t parent, uint8_t hopcount, uint16_t metric) {
		return SUCCESS;
	}
		// Use LEDs to report various status issues.
	static void fatal_problem() { 
		call Leds.led0On(); 
		call Leds.led1On();
		call Leds.led2On();
		call Timer.stop();
	}
	static void report_problem_0() { 
		call Leds.led0Toggle(); 
	}
	static void report_problem_1() { 
		call Leds.led1Toggle();
	}
	static void report_problem_2() { 
		call Leds.led2Toggle();
	}
}
