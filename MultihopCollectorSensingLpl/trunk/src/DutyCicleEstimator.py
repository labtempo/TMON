applicationPacketSize= 80 #size packet of our application
ctpHeaderSize=  208 #size CTP header
ackPacketSize = 88
ctpPacketRouterSize = 560 
ctpPacketsBeaconSend = 1

timePerBitTransmissionMS= 0.004 #time in milliseconds to transmit one bit a 250kb/s

powerTXmA= 21 #power in mA to transmit Iris
powerRXmA= 18 #power in mA to listen Iris
powerLPL= 4 #power in mA to low power listening with Box MAC 1

wakeUpIntervalMS= 512 #interval between listen checks
receiveCheckInterval= 11 # interval to check listen activity
averageSendCicleIntervalMS= 540000 #average interval between sends samples 9 minutes
delayAfterReceive  = 20 # delay radio stay on after or send receive one packet


TimeTXAck= (ackPacketSize * timePerBitTransmissionMS + wakeUpIntervalMS)* ctpPacketsBeaconSend + 1
TimeRXAck= (ackPacketSize * timePerBitTransmissionMS + delayAfterReceive)* ctpPacketsBeaconSend + 1

timeTXApp= ( applicationPacketSize + ctpHeaderSize ) * timePerBitTransmissionMS + wakeUpIntervalMS #time of radioTX on in the worst case
timeRXApp= averageSendCicleIntervalMS/wakeUpIntervalMS * receiveCheckInterval + delayAfterReceive#time of radioRx On


timeTXCTP= (ctpPacketRouterSize * timePerBitTransmissionMS + wakeUpIntervalMS) * ctpPacketsBeaconSend#time of radioTX on in the worst case
timeRXCTP= ctpPacketRouterSize * timePerBitTransmissionMS + delayAfterReceive

timeRadioON = timeTXApp + timeRXApp + timeTXCTP + timeRXCTP
timeRadioOff= averageSendCicleIntervalMS - timeRadioON
dutyCicle = (timeRadioON)/averageSendCicleIntervalMS * 100


print 'Duty cicle of WSN=',dutyCicle,'%'