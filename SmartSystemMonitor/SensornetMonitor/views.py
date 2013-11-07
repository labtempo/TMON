from SensornetMonitor.models import *
from AlertSystem.models import *
from django.shortcuts import render_to_response, get_object_or_404
from SensornetMonitor.forms import *
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.db.transaction import commit
from Shared import *
import datetime
import networkx
import matplotlib.pyplot as plt
from realtime_monitor import *
import pygame
from Shared import verifyALert
from networkx.readwrite import json_graph
import json

def home(request):
    alert = verifyALert()
    average_temperature = AverageTemperature.objects.order_by('-pk')[0]
    average_list = AverageTemperature.objects.filter(timeStamp__gte=datetime.datetime.now() - datetime.timedelta(days=2)).order_by('pk')
    alerts_info = alert_list = Alert.objects.order_by('-id').filter(type__iexact='info')[:5]
    alerts_warning = alert_list = Alert.objects.order_by('-id').filter(type__iexact='warning')[:5]
    alerts_critical = alert_list = Alert.objects.order_by('-id').filter(type__iexact='critical')[:5]
    all_motes_list = Mote.objects.all()
    motes_active = 0
    motes_inactive = 0
    for mote in all_motes_list:
        if mote.status == True:
            motes_active += 1
        else:
            motes_inactive += 1
    total_motes = len(all_motes_list)                    
    return render_to_response('home.html', {'alert':alert,
                                            'average_temperature':average_temperature.temperature,
                                            'average_list':average_list,
                                            'alerts_info':alerts_info,
                                            'alerts_warning':alerts_warning,
                                            'alerts_critical':alerts_critical,
                                            'motes_active':motes_active,
                                            'motes_inactive':motes_inactive,
                                            'total_motes':total_motes})
           
def list(request):
    alert = verifyALert()
    if request.method == "POST":
        form = MoteDetail(request.POST, request.FILES)
        if form.is_valid():
            mote_id = str(form.cleaned_data['id'])
            return detail(request, mote_id)
    else:
        all_motes_list = Mote.objects.all().order_by('id')
        form = MoteDetail()
        return render_to_response('SensornetMonitor/list.html', {'all_motes_list': all_motes_list, 'alert':alert, 'form':form}, context_instance=RequestContext(request))
        

def detail(request, mote_id):
    alert = verifyALert()
    mote = get_object_or_404(Mote, pk=mote_id)
    is_sensor = True
    if mote.id % 10 == 0:
        is_sensor = False
    try:
        samples_list = Sample.objects.filter(mote__exact=mote).filter(timeStamp__gte=datetime.datetime.now() - datetime.timedelta(weeks=1)).order_by('pk')
        sample = samples_list.order_by('-pk')[0]
        remaining_days = calc_battery_life (sample.readingVoltage)
    except:
        remaining_days = 'Unknown'
    return render_to_response('SensornetMonitor/detail.html', {'mote': mote,
                                                               'remaining_days':remaining_days,
                                                               'samples_list':samples_list,
                                                               'is_sensor':is_sensor,
                                                               'alert':alert }, context_instance=RequestContext(request))

def detailDynamic(request):
    alert = verifyALert()
    motes = []
    samples_list = []
    if request.method == "POST":
        form = DynamicViewForm(request.POST, request.FILES)
        if form.is_valid():            
            elementsList = (form.cleaned_data['listIds']).split()
            view_type = form.cleaned_data['view_types']
            samples_list = []
            for element in elementsList:
                if int(element) % 10 == 0 and view_type != 'Battery':
                    return render_to_response('errorimputfields.html')                   
                mote = get_object_or_404(Mote, pk=int(element))
                motes.append(mote)
                samples_list += Sample.objects.filter(mote__exact=mote).exclude(timeStamp__gte=form.cleaned_data['finalDate']).filter(timeStamp__gte=form.cleaned_data['startDate'])
            return render_to_response('SensornetMonitor/detaildynamic.html', {'motes': motes,
                                                                       'samples_list':samples_list,
                                                                       'view_type':view_type,
                                                                       'alert':alert})         
        else:
            return render_to_response('errorimputfields.html')
    else:
        form = DynamicViewForm()
        return render_to_response('SensornetMonitor/dynamicviewform.html', {'form': form, 'alert':alert}, context_instance=RequestContext(request))

def detailInterval(request, mote_id):
    alert = verifyALert()
    if request.method == "POST":
        form = MoteDetailInterval(request.POST, request.FILES)
        if form.is_valid():
            mote = get_object_or_404(Mote, pk=form.cleaned_data['id'])
            is_sensor = True
            if mote.id % 10 == 0:
                is_sensor = False
            try:
                samples_list = Sample.objects.filter(mote__exact=mote).exclude(timeStamp__gte=form.cleaned_data['finalDate']).filter(timeStamp__gte=form.cleaned_data['startDate'])
                sample = samples_list.order_by('-pk')[0]
                remaining_days = calc_battery_life (sample.readingVoltage)
            except:
                remaining_days = 'Unknown'
            return render_to_response('SensornetMonitor/detail.html', {'mote': mote,
                                                                       'remaining_days':remaining_days,
                                                                       'samples_list':samples_list,
                                                                       'is_sensor':is_sensor,
                                                                       'alert':alert})
        else:
            return render_to_response('errorimputfields.html')
    else:
        form = MoteDetailInterval(initial={'id': mote_id})
        return render_to_response('SensornetMonitor/detailintervalform.html', {'form': form, 'alert':alert}, context_instance=RequestContext(request))

@login_required 
def systemStatus (request):
    alert = verifyALert()
    if request.method == "POST":
        form = FormSystemStatus(request.POST, request.FILES)
        try:
            old_status = SystemStatus.objects.order_by('-pk')[0]
        except:
            old_status = SystemStatus.create(False)
        new_status = form.save(commit=False)
        if old_status.status == new_status.status:
            last_change = old_status.timeStatusChanged
            msg = 'The system status is not changed!'            
        else:
            new_status.timeStatusChanged = datetime.datetime.now()
            new_status.save()            
            publish_maintenance(new_status.timeStatusChanged, 'The system status changed, now is ' + new_status.status)
            last_change = new_status.timeStatusChanged
            msg = 'The system status changed with success!'
        data = form.cleaned_data
        if data['status'] == 1:
            msg = msg + ' The system is in maintenance! Since: ' + last_change.strftime("%H:%M %d/%m/%y")
            notify_admin_by_email(msg)
            return render_to_response('SensornetMonitor/statussuccesssalved.html', {'msg': msg, 'alert':alert})
        elif data['status'] == 0:
            msg = msg + ' The system is fully operational! Since: ' + last_change.strftime("%H:%M %d/%m/%y")
            notify_admin_by_email(msg)
            return render_to_response('SensornetMonitor/statussuccesssalved.html', {'msg': msg, 'alert':alert})
        else:
            return render_to_response('SensornetMonitor/errorimputfields.html', {'alert':alert})
    else:
        try:
            status = SystemStatus.objects.order_by('-pk')[0]
        except:
            status = SystemStatus.create(False)
        form = FormSystemStatus(instance=status)
        return render_to_response('SensornetMonitor/systemstatus.html', {'form': form, 'alert':alert}, context_instance=RequestContext(request))
    
def networkGraph (request):
    alert = verifyALert()
    G = networkx.DiGraph()
    G.add_node(0, name='Root', color="27A0D8", size=30)
    bases = []
    bases.append(0)   
    motes_list = Mote.objects.all()
    nodes_active = []
    nodes_inactive = []
    for mote in motes_list:
        try:
            last_sample = Sample.objects.filter(mote__exact=mote).order_by('-pk')[0]
            if mote.status == False:
                if mote.localizationDescription == None:
                    localization = 'Location unavailable'
                else:
                    localization = mote.localizationDescription
                G.add_node(mote.id, name=mote.id, detail=localization, color="red", cost=last_sample.metric, url='/SensornetMonitor/' + str(mote.id) + '/')
            else:
                if mote.localizationDescription == None:
                    localization = 'Location unavailable'
                else:
                    localization = mote.localizationDescription
                G.add_node(mote.id, name=mote.id, detail=localization, color="green", cost=last_sample.metric, url='/SensornetMonitor/' + str(mote.id) + '/', label=last_sample.metric)
            G.add_edge(last_sample.parent, mote.id, label=last_sample.metric)
        except Exception, e:
            print e
    d = json_graph.tree_data(G, root=0)  # node-link format to serialize    
    json.dump(d, open('Media/networkgraph/force.json', 'w'))
    return render_to_response('SensornetMonitor/networkgraph.html', {'alert':alert})

def thermalMap (request):
    min_temp = 15
    max_temp = 65
    alert = verifyALert()
    form = ThermalMapView()
    if request.method == "POST":
        form = ThermalMapView(request.POST, request.FILES)
        if form.is_valid():
            view_type = form.cleaned_data['view_types']
            view_choices = form.cleaned_data['view_choices']
            
            config = ConfigParser.ConfigParser()
            file = open("Media/Param.conf", "w")
            config.add_section('thermalMap')
            config.set('thermalMap','view_choices',view_choices)
            config.set('thermalMap','view_type',view_type)
            config.write(file)
            file.close()
           
        # Thermal map generator
        if view_type == 'Top':
            room = ObjectDatacenter.objects.filter(type__exact="Room")[0]
            rack_list = ObjectDatacenter.objects.filter(type__exact="Rack")
            mote_list = ObjectDatacenter.objects.filter(type__exact="Mote")
            for mote in mote_list:
                mote.localizationX = mote.parent.localizationX + mote.localizationX
                mote.localizationY = mote.parent.localizationY + mote.localizationY
            sample_list = []
            for obj in mote_list:
                    mote = get_object_or_404(Mote, pk=obj.mote.id)
                    sample_list.append(Sample.objects.filter(mote__exact=mote).order_by('-pk')[0])
            if view_choices == 'Relative':
                max_temp = float('-inf')
                min_temp = float('+inf')
                for sample in sample_list:
                    if sample.readingTemperature > max_temp:
                        max_temp = sample.readingTemperature
                    if sample.readingTemperature < min_temp:
                        min_temp = sample.readingTemperature   
            for obj in mote_list:
                for sample in sample_list:
                    if(obj.mote.id == sample.mote.id):
                        obj.temp = sample.readingTemperature;
                        del(sample); 
                                                         
        if view_type == 'Back':
            room = ObjectDatacenter.objects.filter(type__exact="Room")[0]
            rack_list = ObjectDatacenter.objects.filter(type__exact="Rack")
            for rack in rack_list:
                rack.localizationZ = (rack.parent.localizationZ+rack.localizationZ)*-1+(rack.parent.height-rack.height)
                
            mote_list = ObjectDatacenter.objects.filter(type__exact="Mote").filter(localizationY__gte=2)
            for mote in mote_list:
                mote.localizationX = mote.parent.localizationX + mote.localizationX
                mote.localizationY = mote.parent.localizationY + mote.localizationY
                try:
                    mote.localizationZ = (mote.parent.localizationZ + mote.localizationZ)*-1+mote.parent.height+(mote.parent.parent.height-mote.parent.height)
                except Exception, e:
                    mote.localizationZ = (mote.parent.localizationZ + mote.localizationZ)*-1+mote.parent.height
            sample_list = []
            for obj in mote_list:
                    mote = get_object_or_404(Mote, pk=obj.mote.id)
                    sample_list.append(Sample.objects.filter(mote__exact=mote).order_by('-pk')[0])
            if view_choices == 'Relative':
                max_temp = float('-inf')
                min_temp = float('+inf')
                for sample in sample_list:
                    if sample.readingTemperature > max_temp:
                        max_temp = sample.readingTemperature
                    if sample.readingTemperature < min_temp:
                        min_temp = sample.readingTemperature   
            for obj in mote_list:
                for sample in sample_list:
                    if(obj.mote.id == sample.mote.id):
                        obj.temp = sample.readingTemperature;
                        del(sample);
        
        if view_type == 'Front':
            room = ObjectDatacenter.objects.filter(type__exact="Room")[0]
            rack_list = ObjectDatacenter.objects.filter(type__exact="Rack")
            for rack in rack_list:
                rack.localizationX = (rack.parent.localizationX+rack.localizationX)*-1+(rack.parent.width-rack.width)
                rack.localizationZ = (rack.parent.localizationZ+rack.localizationZ)*-1+(rack.parent.height-rack.height)
                
            mote_list = ObjectDatacenter.objects.filter(type__exact="Mote").exclude(localizationY__gte=2)
            for mote in mote_list:
                mote.localizationY = mote.parent.localizationY + mote.localizationY
                try:
                    mote.localizationZ = (mote.parent.localizationZ + mote.localizationZ)*-1+mote.parent.height+(mote.parent.parent.height-mote.parent.height)
                    mote.localizationX = (mote.parent.localizationX + mote.localizationX)*-1+mote.parent.width+(mote.parent.parent.width-mote.parent.width)
                except Exception, e:
                    mote.localizationZ = (mote.parent.localizationZ + mote.localizationZ)*-1+mote.parent.height
                    mote.localizationX = (mote.parent.localizationX + mote.localizationX)*-1+mote.parent.width
            sample_list = []
            for obj in mote_list:
                    mote = get_object_or_404(Mote, pk=obj.mote.id)
                    sample_list.append(Sample.objects.filter(mote__exact=mote).order_by('-pk')[0])
            if view_choices == 'Relative':
                max_temp = float('-inf')
                min_temp = float('+inf')
                for sample in sample_list:
                    if sample.readingTemperature > max_temp:
                        max_temp = sample.readingTemperature
                    if sample.readingTemperature < min_temp:
                        min_temp = sample.readingTemperature   
            for obj in mote_list:
                for sample in sample_list:
                    if(obj.mote.id == sample.mote.id):
                        obj.temp = sample.readingTemperature;
                        del(sample);     
        return render_to_response('SensornetMonitor/thermalmapviewform.html', {'form': form, 'alert':alert, 'room':room, 'rack_list': rack_list, 'mote_list':mote_list, 'max_temp':max_temp, 'min_temp':min_temp, 'view_type':view_type}, context_instance=RequestContext(request))
    else:
        view_choices =  readConfig('thermalMap','view_choices')
        view_type = readConfig('thermalMap','view_type')
        
         # Thermal map generator
        if view_type == 'Top':
            room = ObjectDatacenter.objects.filter(type__exact="Room")[0]
            rack_list = ObjectDatacenter.objects.filter(type__exact="Rack")
            mote_list = ObjectDatacenter.objects.filter(type__exact="Mote")
            for mote in mote_list:
                mote.localizationX = mote.parent.localizationX + mote.localizationX
                mote.localizationY = mote.parent.localizationY + mote.localizationY
            sample_list = []
            for obj in mote_list:
                    mote = get_object_or_404(Mote, pk=obj.mote.id)
                    sample_list.append(Sample.objects.filter(mote__exact=mote).order_by('-pk')[0])
            if view_choices == 'Relative':
                max_temp = float('-inf')
                min_temp = float('+inf')
                for sample in sample_list:
                    if sample.readingTemperature > max_temp:
                        max_temp = sample.readingTemperature
                    if sample.readingTemperature < min_temp:
                        min_temp = sample.readingTemperature   
            for obj in mote_list:
                for sample in sample_list:
                    if(obj.mote.id == sample.mote.id):
                        obj.temp = sample.readingTemperature;
                        del(sample); 
                                                         
        if view_type == 'Back':
            room = ObjectDatacenter.objects.filter(type__exact="Room")[0]
            rack_list = ObjectDatacenter.objects.filter(type__exact="Rack")
            for rack in rack_list:
                rack.localizationZ = (rack.parent.localizationZ+rack.localizationZ)*-1+(rack.parent.height-rack.height)
                
            mote_list = ObjectDatacenter.objects.filter(type__exact="Mote").filter(localizationY__gte=2)
            for mote in mote_list:
                mote.localizationX = mote.parent.localizationX + mote.localizationX
                mote.localizationY = mote.parent.localizationY + mote.localizationY
                try:
                    mote.localizationZ = (mote.parent.localizationZ + mote.localizationZ)*-1+mote.parent.height+(mote.parent.parent.height-mote.parent.height)
                except Exception, e:
                    mote.localizationZ = (mote.parent.localizationZ + mote.localizationZ)*-1+mote.parent.height
            sample_list = []
            for obj in mote_list:
                    mote = get_object_or_404(Mote, pk=obj.mote.id)
                    sample_list.append(Sample.objects.filter(mote__exact=mote).order_by('-pk')[0])
            if view_choices == 'Relative':
                max_temp = float('-inf')
                min_temp = float('+inf')
                for sample in sample_list:
                    if sample.readingTemperature > max_temp:
                        max_temp = sample.readingTemperature
                    if sample.readingTemperature < min_temp:
                        min_temp = sample.readingTemperature   
            for obj in mote_list:
                for sample in sample_list:
                    if(obj.mote.id == sample.mote.id):
                        obj.temp = sample.readingTemperature;
                        del(sample);
        
        if view_type == 'Front':
            room = ObjectDatacenter.objects.filter(type__exact="Room")[0]
            rack_list = ObjectDatacenter.objects.filter(type__exact="Rack")
            for rack in rack_list:
                rack.localizationX = (rack.parent.localizationX+rack.localizationX)*-1+(rack.parent.width-rack.width)
                rack.localizationZ = (rack.parent.localizationZ+rack.localizationZ)*-1+(rack.parent.height-rack.height)
                
            mote_list = ObjectDatacenter.objects.filter(type__exact="Mote").exclude(localizationY__gte=2)
            for mote in mote_list:
                mote.localizationY = mote.parent.localizationY + mote.localizationY
                try:
                    mote.localizationZ = (mote.parent.localizationZ + mote.localizationZ)*-1+mote.parent.height+(mote.parent.parent.height-mote.parent.height)
                    mote.localizationX = (mote.parent.localizationX + mote.localizationX)*-1+mote.parent.width+(mote.parent.parent.width-mote.parent.width)
                except Exception, e:
                    mote.localizationZ = (mote.parent.localizationZ + mote.localizationZ)*-1+mote.parent.height
                    mote.localizationX = (mote.parent.localizationX + mote.localizationX)*-1+mote.parent.width
            sample_list = []
            for obj in mote_list:
                    mote = get_object_or_404(Mote, pk=obj.mote.id)
                    sample_list.append(Sample.objects.filter(mote__exact=mote).order_by('-pk')[0])
            if view_choices == 'Relative':
                max_temp = float('-inf')
                min_temp = float('+inf')
                for sample in sample_list:
                    if sample.readingTemperature > max_temp:
                        max_temp = sample.readingTemperature
                    if sample.readingTemperature < min_temp:
                        min_temp = sample.readingTemperature   
            for obj in mote_list:
                for sample in sample_list:
                    if(obj.mote.id == sample.mote.id):
                        obj.temp = sample.readingTemperature;
                        del(sample);    
        return render_to_response('SensornetMonitor/thermalmapviewform.html', {'form': form, 'alert':alert, 'room':room, 'rack_list': rack_list, 'mote_list':mote_list, 'max_temp':max_temp, 'min_temp':min_temp, 'view_type':view_type}, context_instance=RequestContext(request))