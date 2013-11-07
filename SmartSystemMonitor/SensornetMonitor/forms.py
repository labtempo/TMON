from django import forms
import datetime
from django.core.context_processors import request
from models import SystemStatus, Mote
from bootstrap_toolkit.widgets import BootstrapDateInput
from django.template.defaultfilters import default
from Shared import readConfig


class MoteDetailInterval(forms.Form):
    id = forms.IntegerField(label='Mote ID', required=True, help_text='Id of mote to detail')
    startDate = forms.DateTimeField(label='Initial period', required=True, widget=BootstrapDateInput())
    finalDate = forms.DateTimeField(label='Final period', initial=datetime.datetime.now(), required=True, widget=BootstrapDateInput())
    
class MoteDetail(forms.Form):
    id = forms.ModelChoiceField(label='Mote ID', required=True, help_text='Id of mote to detail', queryset=Mote.objects.all().order_by('id'))

class FormSystemStatus(forms.ModelForm):
    class Meta:
        model = SystemStatus
    
class ThermalMapView(forms.Form):
    VIEW_TYPES_CHOICES = (
        (u'Top', u'Top'),
        (u'Front', u'Front'),
        (u'Back', u'Back'),
    )
    LEVEL_VIEW_CHOICES = (
        (u'0', u'0'),
        (u'1', u'1'),
        (u'2', u'2'),
        (u'3', u'3'),
        (u'4', u'4'),
        (u'5', u'5'),
        (u'6', u'6'),
        (u'7', u'7'),
        (u'8', u'8'),
    )
    VIEW_CHOICES = (
        (u'Absolute',u'Absolute'),
        (u'Relative',u'Relative'),
        )    
    view_types = forms.ChoiceField(label='Visualization', choices=VIEW_TYPES_CHOICES, help_text="Select one view", initial=readConfig('thermalMap','view_type'))
    view_choices = forms.ChoiceField(label='View type', choices=VIEW_CHOICES, initial=readConfig('thermalMap','view_choices'))

    # level_view = forms.ChoiceField(label='Level view', choices=LEVEL_VIEW_CHOICES, help_text="Insert zoom level of visualization", initial='0')
    
    
class DynamicViewForm(forms.Form):
    VIEW_TYPES_CHOICES = (
        (u'Temperature', u'temperature'),
        (u'Light', u'light'),
        (u'Battery', u'battery'),
    )
    listIds = forms.CharField(label='List of IDs', required=True, help_text='Motes separated by spaces.', max_length=50)
    view_types = forms.TypedChoiceField(label='Views', choices=VIEW_TYPES_CHOICES, help_text=u'Select one view', initial='temperature')
    startDate = forms.DateTimeField(label='Initial period', initial=datetime.datetime.now() - datetime.timedelta(weeks=1), widget=BootstrapDateInput())  # widget= forms.DateTimeInput(format='%H:%M %d/%m/%Y')
    finalDate = forms.DateTimeField(label='Final period', initial=datetime.datetime.now(), widget=BootstrapDateInput())
    
