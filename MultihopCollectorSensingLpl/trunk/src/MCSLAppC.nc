/**
 * MCSLC exercises the basic networking layers, collection and
 * dissemination. The application samples DemoSensorC at a basic rate
 * and sends packets up a collection tree. The rate is configurable
 * through dissemination.
 *
 * See TEP118: Dissemination, TEP 119: Collection, and TEP 123: The
 * Collection Tree Protocol for details.
 * 
 * @author Philip Levis
 * @version $Revision: 1.1 $ $Date: 2009-09-16 00:53:47 $
 */
#include "MCSL.h"
#include "Ctp.h"

configuration MCSLAppC {
}
implementation {
	components MCSLC, MainC, LedsC, ActiveMessageC;
	components DisseminationC;
	components new DisseminatorC(uint32_t, SAMPLE_RATE_KEY) as Object32C;
	components CollectionC as Collector;
	components new CollectionSenderC(SAMPLES);
	components new TimerMilliC();
	components new SerialAMSenderC(SAMPLES);
	components SerialActiveMessageC;

	components RandomC;
	components new QueueC(message_t *, 12);
	components new PoolC(message_t, 12);
	components new TempC() as TempSensor;
	components new PhotoC() as PhotoSensor;
	components new VoltageC() as VoltageSensor;

	components DelugeC;
	components LedsC as LedsDeluge;
	DelugeC.Leds->LedsDeluge;

	#ifndef NO_DEBUG
	components new SerialAMSenderC(AM_COLLECTION_DEBUG) as UARTSender;
	components UARTDebugSenderP as DebugSender;
	#endif

	MCSLC.Boot->MainC;
	MCSLC.RadioControl->ActiveMessageC;
	MCSLC.SerialControl->SerialActiveMessageC;
	MCSLC.RoutingControl->Collector;
	MCSLC.DisseminationControl->DisseminationC;
	MCSLC.Leds->LedsC;
	MCSLC.Timer->TimerMilliC;
	MCSLC.DisseminationPeriod->Object32C;
	MCSLC.Send->CollectionSenderC;
	MCSLC.Temp->TempSensor;
	MCSLC.Light->PhotoSensor;
	MCSLC.Volt->VoltageSensor;
	MCSLC.RootControl->Collector;
	MCSLC.Receive->Collector.Receive[SAMPLES];
	MCSLC.UARTSend->SerialAMSenderC.AMSend;
	MCSLC.CollectionPacket->Collector;
	MCSLC.CtpInfo -> Collector;
	MCSLC.CtpCongestion->Collector;
	MCSLC.Random->RandomC;
	MCSLC.Pool->PoolC;
	MCSLC.Queue->QueueC;
	MCSLC.RadioPacket->ActiveMessageC;
	MCSLC.LowPowerListening->ActiveMessageC;

	#ifndef NO_DEBUG
	components new PoolC(message_t, 10) as DebugMessagePool;
	components new QueueC(message_t *, 10) as DebugSendQueue;
	DebugSender.Boot->MainC;
	DebugSender.UARTSend->UARTSender;
	DebugSender.MessagePool->DebugMessagePool;
	DebugSender.SendQueue->DebugSendQueue;
	Collector.CollectionDebug->DebugSender;
	MCSLC.CollectionDebug->DebugSender;
	#endif
	MCSLC.AMPacket->ActiveMessageC;
}