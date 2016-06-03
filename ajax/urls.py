from __future__ import absolute_import
from django.conf.urls import *
from django.views.static import serve
from ajax import views
import django
import os

JAVASCRIPT_PATH = "%s/js" % os.path.dirname(__file__)

if django.VERSION < (1, 8):
    urlpatterns = patterns('ajax.views',
        (r'^(?P<application>\w+)/(?P<model>\w+).json', 'endpoint_loader'),
        (r'^(?P<application>\w+)/(?P<model>\w+)/(?P<method>\w+).json', 'endpoint_loader'),
        (r'^(?P<application>\w+)/(?P<model>\w+)/(?P<pk>\d+)/(?P<method>\w+)/?(?P<taggit_command>(add|remove|set|clear|similar))?.json$', 'endpoint_loader'),
        (r'^js/(?P<path>.*)$', serve,
            {'document_root': JAVASCRIPT_PATH}),
    )
else:
    urlpatterns = [
        url(r'^(?P<application>\w+)/(?P<model>\w+).json', views.endpoint_loader),
        url(r'^(?P<application>\w+)/(?P<model>\w+)/(?P<method>\w+).json', views.endpoint_loader),
        url(r'^(?P<application>\w+)/(?P<model>\w+)/(?P<pk>\d+)/(?P<method>\w+)/?(?P<taggit_command>(add|remove|set|clear|similar))?.json$', views.endpoint_loader),
        url(r'^js/(?P<path>.*)$', serve,
            {'document_root': JAVASCRIPT_PATH}),
    ]
