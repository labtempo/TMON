#!/usr/bin/env python
from django.core.management import setup_environ
import settings
from symbol import except_clause
setup_environ(settings)

import datetime
import pika
import string
from pika import channel
from Shared import *
from SensornetMonitor.models import Sample, Mote, SystemStatus, AverageTemperature

def persistEvent(event):
    data_sample = event.split()
    try:
        mote = Mote.objects.get(pk=int(data_sample[3]))
    except:
        mote = Mote.create(int(data_sample[3]))
        publish(ALERT_WARNING, datetime.datetime.now(), 'Mote ID: ' + str(mote.id) + '  joined, insert its location', EXCHANGE_MOTE_STATUS)
        mote.save()
    sample = Sample.create(str(data_sample[1] + ' ' + data_sample[2]),
                           mote,
                           int(data_sample[4]),
                           float(data_sample[5]),
                           int(data_sample[6]),
                           float(data_sample[7]),
                           int(data_sample[8]),
                           int(data_sample[9]))
    sample.save()
                

def callback(ch, method, properties, event):
    print " Reading received %r: " % (event)
    persistEvent(event)
    
def averageSave():
    all_motes_list = Mote.objects.filter(status__exact=True)
    if len(all_motes_list) == 0:
        publish(ALERT_CRITICAL, datetime.datetime.now(), 'WSN is down!', EXCHANGE_MOTE_STATUS)
    temperatures = 0
    motes_temperature = 0
    for mote in all_motes_list:
       last_sample = Sample.objects.filter(mote__exact=mote).order_by('-pk')[0]
       temperatures += last_sample.readingTemperature
       if mote.id % 10 != 0:
           motes_temperature += 1
    try:
        average_temperature = AverageTemperature.create(temperatures / motes_temperature)
        average_temperature.save()
    except:
        print 
        average_temperature = AverageTemperature.create(0)
        average_temperature.save()        
    
def checkMotesInactive():
    averageSave()
    try:
        last_system_status = SystemStatus.objects.all().order_by('-pk')[0]
        system_status = last_system_status.status        
    except:
        system_status = False
    try:                    
        motes = Mote.objects.all()
        time_now = datetime.datetime.now()
        for mote in motes:
            try:
                last_sample = Sample.objects.filter(mote__exact=mote).order_by('-pk')[0]
                if ((time_now - datetime.timedelta(minutes=6)) > last_sample.timeStamp) and (mote.status == True) and (system_status == False): 
                    mote.status = False
                    publish(ALERT_WARNING, time_now, 'Mote ' + str(mote.id) + ' is down', EXCHANGE_MOTE_STATUS)
                    mote.save()
                elif ((time_now - datetime.timedelta(minutes=5)) < last_sample.timeStamp) and (mote.status == False):
                    mote.status = True
                    publish(ALERT_WARNING, time_now, 'Mote ' + str(mote.id) + ' back to the network', EXCHANGE_MOTE_STATUS)
                    mote.save()
                if (calc_battery_life(last_sample.readingVoltage) < 3)and (mote.status == True) and (system_status == False):
                    publish(ALERT_WARNING, time_now, 'Mote ' + str(mote.id) + ' battery is low', EXCHANGE_MOTE_STATUS)
            except IndexError:
                publish(ALERT_WARNING, time_now, 'Mote  ' + str(mote.id) + ' no has samples', EXCHANGE_MOTE_STATUS)
    except:
        message = 'Error in connection to the database!'
        print message
        notify_admin_by_email(message)
    

def main():
    # Check motes status every 60 seconds
    interval_monitor = setInterval(checkMotesInactive, 60)
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=EVENT_SERVER))
        channel = connection.channel()    
        channel.exchange_declare(exchange=EXCHANGE_READINGS, type='fanout')    
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue    
        channel.queue_bind(exchange=EXCHANGE_READINGS, queue=queue_name)
    except Exception, e:
        print("Error %s:" % e.args[0])
    finally:        
        print 'Waiting for readings. To exit press CTRL+C'
    
    channel.basic_consume(callback, queue=queue_name, no_ack=True)
    try:
        channel.start_consuming()
    except:
        message = 'Error in connection to the event server'
        print message
        notify_admin_by_email(message)
        
    
if __name__ == "__main__":
    main()
    
