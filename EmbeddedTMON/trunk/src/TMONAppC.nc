/**
 * TMON exercises the basic networking layers, collection and
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
#include "TMON.h"
#include "Ctp.h"

configuration TMONAppC {
}
implementation {
	components TMONC, MainC, LedsC, ActiveMessageC;
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

	TMONC.Boot->MainC;
	TMONC.RadioControl->ActiveMessageC;
	TMONC.SerialControl->SerialActiveMessageC;
	TMONC.RoutingControl->Collector;
	TMONC.DisseminationControl->DisseminationC;
	TMONC.Leds->LedsC;
	TMONC.Timer->TimerMilliC;
	TMONC.DisseminationPeriod->Object32C;
	TMONC.Send->CollectionSenderC;
	TMONC.Temp->TempSensor;
	TMONC.Light->PhotoSensor;
	TMONC.Volt->VoltageSensor;
	TMONC.RootControl->Collector;
	TMONC.Receive->Collector.Receive[SAMPLES];
	TMONC.UARTSend->SerialAMSenderC.AMSend;
	TMONC.CollectionPacket->Collector;
	TMONC.CtpInfo -> Collector;
	TMONC.CtpCongestion->Collector;
	TMONC.Random->RandomC;
	TMONC.Pool->PoolC;
	TMONC.Queue->QueueC;
	TMONC.RadioPacket->ActiveMessageC;
	TMONC.LowPowerListening->ActiveMessageC;

	#ifndef NO_DEBUG
	components new PoolC(message_t, 10) as DebugMessagePool;
	components new QueueC(message_t *, 10) as DebugSendQueue;
	DebugSender.Boot->MainC;
	DebugSender.UARTSend->UARTSender;
	DebugSender.MessagePool->DebugMessagePool;
	DebugSender.SendQueue->DebugSendQueue;
	Collector.CollectionDebug->DebugSender;
	TMONC.CollectionDebug->DebugSender;
	#endif
	TMONC.AMPacket->ActiveMessageC;
	
	components TimeSyncMessageC;
	components TimeSyncC;
	MainC.SoftwareInit -> TimeSyncC;
	TimeSyncC.Boot -> MainC;	
	TMONC.TimeSyncPacket -> TimeSyncMessageC;
	TMONC.PacketTimeStamp -> ActiveMessageC;
	TMONC.GlobalTime -> TimeSyncC;
	TMONC.TimeSyncInfo -> TimeSyncC;
	
//	components PrintfC;
//  	components SerialStartC;	
}