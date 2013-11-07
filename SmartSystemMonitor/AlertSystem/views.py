from AlertSystem.models import Alert
from django.shortcuts import render_to_response
from django.template import RequestContext
from AlertSystem.forms import LogInterval
from django.contrib.auth.decorators import login_required
from Shared import verifyALert
import datetime


def list(request):
    alert = verifyALert()
    form = LogInterval()
    all_alert_list = Alert.objects.all().order_by('-id')
    return render_to_response('AlertSystem/list.html', {'all_alert_list': all_alert_list,'form': form, 'alert':alert}, context_instance=RequestContext(request))

def logInterval(request):
    alert = verifyALert()
    form = LogInterval()
    if request.method == "POST":
        form = LogInterval(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['finalDate'] == form.cleaned_data['startDate']:
                alert_list = Alert.objects.all().order_by('id').filter(type__iexact=form.cleaned_data['log_type']).exclude(timeStamp__gte=form.cleaned_data['finalDate'] + datetime.timedelta(days=1)).filter(timeStamp__gte=form.cleaned_data['startDate'])
            else:
                alert_list = Alert.objects.all().order_by('id').filter(type__iexact=form.cleaned_data['log_type']).exclude(timeStamp__gte=form.cleaned_data['finalDate']).filter(timeStamp__gte=form.cleaned_data['startDate'])
            return render_to_response('AlertSystem/list.html', {'all_alert_list': alert_list, 'alert':alert,'form': form}, context_instance=RequestContext(request))
        else:
            return render_to_response('errorimputfields.html',{'alert':alert})
    else:
        alert_list = Alert.objects.filter(timeStamp__gte=datetime.datetime.now() - datetime.timedelta(days=1))
        return render_to_response('AlertSystem/list.html', {'all_alert_list': alert_list,'form': form, 'alert':alert}, context_instance=RequestContext(request))