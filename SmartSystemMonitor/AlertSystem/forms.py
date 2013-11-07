from django import forms
import datetime
from django.core.context_processors import request
from bootstrap_toolkit.widgets import BootstrapDateInput

class LogInterval(forms.Form):
     LOGS_TYPES_CHOICES = (
        (u'Warning', u'warning'),
        (u'Info', u'info'),
        (u'Critical', u'critical'),
        )
     startDate = forms.DateTimeField(label='Initial period',  required = True, help_text = 'Insert initial time and date for log consult', widget=BootstrapDateInput())#widget= forms.DateTimeInput(format='%H:%M %d/%m/%Y'),
     finalDate = forms.DateTimeField(label='Final period',  initial = datetime.datetime.now(), required = True, help_text = 'Insert final time and date for log consult', widget=BootstrapDateInput())
     log_type = forms.ChoiceField(label='Log type', choices=LOGS_TYPES_CHOICES, help_text="Select log type to view", initial='Warning')
