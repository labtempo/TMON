from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.core.mail import mail_admins
from AlertSystem.models import Alert
import datetime
import ConfigParser


import pika  # component to access Event Manager
from AlertSystem.models import Alert

from threading import Timer

# E-mails configurations
EMAIL_SUBJECT = 'Smart System Monitor'
EMAIL_ADDRESS = 'notification@tempo.uff.br'

# #Event Server IP address
EVENT_SERVER = '200.20.15.53'  # TMON server

# Channels
EXCHANGE_READINGS = 'readings'
EXCHANGE_MAINTENANCE = 'maintenance'
EXCHANGE_MOTE_STATUS = 'mote_status'

# Type of alerts
ALERT_INFO = 'info'
ALERT_WARNING = 'warning'
ALERT_CRITICAL = 'critical'

def publish(alert_type, timestamp, msg, exchange_channel):
    try:        
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=EVENT_SERVER))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange_channel, type='fanout')
        event = "%s %s %s" % (alert_type, timestamp, msg)
        channel.basic_publish(exchange=exchange_channel, routing_key='', body=event)
        connection.close()
    except:
        print 'Error in publish alert: %s!' % (msg)        
    try:
        if alert_type == 'info':
            id_mote = msg.split()
            alert = Alert.create(alert_type, timestamp, 'The node ' + id_mote[0] + ' sent data', exchange_channel)
            alert.save()
        else:
            alert = Alert.create(alert_type, timestamp, msg, exchange_channel)
            alert.save()
    except:
        print 'Error in save alert: %s!' % (msg)        
        setup_environ(settings)
        
def publish_maintenance(timestamp, status):
    publish(ALERT_WARNING, timestamp, status, EXCHANGE_MAINTENANCE)
        
def calc_battery_life (voltage):
    return int((voltage - 1.8) / 0.023)        


def setInterval(function, interval, *params, **kwparams):
    def setTimer(wrapper):
        wrapper.timer = Timer(interval, wrapper)
        wrapper.timer.start()

    def wrapper():
        function(*params, **kwparams)
        setTimer(wrapper)
    
    setTimer(wrapper)
    return wrapper

def clearInterval(wrapper):
    wrapper.timer.cancel()
    
def notify_admin_by_email(msg):
    # mail_admins(EMAIL_SUBJECT, msg)
    pass

def verifyALert():
    alert = Alert.objects.order_by('-pk')[0]
    if datetime.datetime.now() - datetime.timedelta(seconds=30) <= alert.timeStamp:
        return alert   


    
def readConfig (section, param):
    config = ConfigParser.ConfigParser()
    config.read("Media/Param.conf")
    result = config.get(section, param)
    return result
