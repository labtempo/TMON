from django.db import models
import datetime

# Mote informations
class Mote (models.Model):
    MOTE_MODEL_CHOICES = (
        (u'Iris', u'iris'),
        (u'Micaz', u'micaz'),
    )
    MOTE_LOCALIZATION_CHOICES = (
        (u'Inlet', u'inlet'),
        (u'Outlet', u'outlet'),
        (u'On Rack', u'on rack'),
        (u'Router', u'router'),
        (u'Other', u'other'),
    )
    
    id = models.IntegerField(primary_key=True, help_text="Id of mote installation", blank=False)
    status = models.BooleanField(blank=False, editable=False, default=True)
    moteModel = models.CharField(verbose_name='Mote Model', max_length=5, choices=MOTE_MODEL_CHOICES, help_text="iris or micaz",default='iris')
    moteLocalization = models.CharField(verbose_name='Mote localization', max_length=6, choices=MOTE_LOCALIZATION_CHOICES, help_text="Inlet Outlet, ...", blank=True, null=True)
    localizationDescription = models.CharField(verbose_name='Localization Description', max_length=100, help_text="Text description of mote local of installation", blank=True, null=True)

   
    @classmethod
    def create(cls, id):
        mote = cls(id=id, status=True, moteModel='Iris' )
        return mote
    
    def __unicode__(self):
        return '%s' % (self.id)
    class Meta:
        verbose_name = 'Mote'
        verbose_name_plural = 'Motes'
        ordering = ['id']
    
# reading samples informations (timestamp, msg.id, msg.sendCount, raw_to_celcius(msg.readingTemperature), msg.readingLight, voltage)
class Sample (models.Model):
    timeStamp = models.DateTimeField(blank=False)
    mote = models.ForeignKey(Mote)
    sendCount = models.IntegerField(blank=False)
    readingTemperature = models.FloatField(blank=False)
    readingLight = models.IntegerField(blank=False)
    readingVoltage = models.FloatField(blank=False)
    parent = models.IntegerField(editable=False)
    metric = models.IntegerField(editable=False)
    
    @classmethod
    def create(cls, timeStamp, mote, sendCount, readingTemperature, readingLight, readingVoltage, parent, metric):
        sample = cls(timeStamp=timeStamp,
                     mote=mote,
                     sendCount=sendCount,
                     readingTemperature=readingTemperature,
                     readingLight=readingLight,
                     readingVoltage=readingVoltage,
                     parent=parent,
                     metric=metric)
        return sample
    
    def __unicode__(self):
        return '    %s    |     %s    |    %s    |    %s    |    %s    ' % (self.id, self.mote.id, self.readingTemperature, self.readingLight,self.readingVoltage)
    
class SystemStatus(models.Model):
    status = models.BooleanField(blank=False, help_text="Check box to setup the system in the maintenance status \n or uncheck to setup the status for fully operational.")
    timeStatusChanged = models.DateTimeField(editable=False)
    
    @classmethod
    def create(cls, status):
        system_status = cls(status=status, timeStatusChanged=datetime.datetime.now())
        return system_status
    
    def __unicode__(self):
        return self
    
class ObjectDatacenter(models.Model):
    OBJECT_TYPES_CHOICES = (
        (u'Rack', u'rack'),
        (u'Mote', u'mote'),
        (u'Room', u'room'),
    )
    
    
    label = models.CharField(verbose_name='Label Object', max_length=50, help_text="Text description of object in datacenter")
    parent  = models.ForeignKey('ObjectDatacenter', null=True, blank=True)
    #parent = models.IntegerField(verbose_name='Parent of the Object', blank=True, null=True)
    type = models.CharField(verbose_name='Object type', max_length=10, choices=OBJECT_TYPES_CHOICES,default='server')
    mote = models.OneToOneField(Mote, blank=True, null=True,help_text="If object is a mote.")
    
    width = models.IntegerField(verbose_name='Width', help_text="Width of the object")
    length = models.IntegerField(verbose_name='Length', help_text="Length of the object")
    height = models.IntegerField(verbose_name='Height', help_text="Height of the object")
    
    localizationX = models.IntegerField(verbose_name='Localization X', help_text="Value of X localization based in plan cartesian coordinate system")
    localizationY = models.IntegerField(verbose_name='Localization Y', help_text="Value of Y localization based in plan cartesian coordinate system")
    localizationZ = models.IntegerField(verbose_name='Localization Z', help_text="Value of Z localization based in plan cartesian coordinate system")
    
    limitThermal = models.IntegerField(verbose_name='Thermal limit', help_text="Thermal limit of equipment in Celsius")

    
    def __unicode__(self):
        return '    %s    |     %s    ' % (self.label, self.type )
    
class AverageTemperature(models.Model):
    timeStamp = models.DateTimeField()
    temperature = models.FloatField()
    @classmethod
    def create(cls, temperature):
        averageTemperature = cls(timeStamp=datetime.datetime.now(), temperature=temperature)
        return averageTemperature
    
    def __unicode__(self):
        return self
    


    
    
    


        
