from django.conf.urls.defaults import patterns, include, url
from SmartSystemMonitor.SensornetMonitor.models import Mote
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import direct_to_template

admin.autodiscover()

info_dict = {
             'queryset': Mote.objects.all(),
}

urlpatterns = patterns('',
    (r'^contact$', direct_to_template, {'template': 'contact.html'}, "contact"),
    (r'^$','SensornetMonitor.views.home'),
    (r'^SensornetMonitor/list/$','SensornetMonitor.views.list'),
    (r'^SensornetMonitor/detailinterval/(?P<mote_id>\d+)/$','SensornetMonitor.views.detailInterval'),
    (r'^SensornetMonitor/systemstatus/$','SensornetMonitor.views.systemStatus'),
    (r'^SensornetMonitor/networkgraph/$','SensornetMonitor.views.networkGraph'),
    (r'^SensornetMonitor/(?P<mote_id>\d+)/$', 'SensornetMonitor.views.detail'),
    (r'^SensornetMonitor/thermalmap/$', 'SensornetMonitor.views.thermalMap'),
    (r'^SensornetMonitor/detaildynamic/$', 'SensornetMonitor.views.detailDynamic'),
    (r'^AlertSystem/loginterval/alertlist/$','AlertSystem.views.list'),
    (r'^AlertSystem/loginterval/$','AlertSystem.views.logInterval'),
    (r'^admin/', include(admin.site.urls)),
    (r'^login/', "django.contrib.auth.views.login",{'template_name': 'admin/login.html'}),
    (r'^logout/', "django.contrib.auth.views.logout_then_login", {'login_url': '/login/'}),
)

if settings.DEBUG:
    urlpatterns += patterns ('',
                             (r'^media/(?P<path>.*)$','django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
                             )

