from django.db import models

class Alert (models.Model):
    type = models.CharField(verbose_name='Type of alert', max_length=10, help_text='Severity level of the alert', editable=False)
    timeStamp = models.DateTimeField(verbose_name='Time of alert', editable=False)
    event = models.CharField(verbose_name='Event description', max_length=100, help_text='Text description of event', editable=False)    
    channel = models.CharField(verbose_name='Channel of alert', max_length=20, help_text='Channel origin of the alert', editable=False)
    
    @classmethod
    def create(cls, alertType, timeStamp, event, alertChannel):
        alert = cls(type=alertType, timeStamp=timeStamp, event=event, channel=alertChannel)
        return alert

    def __unicode__(self):
        return self