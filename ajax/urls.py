from django.conf.urls.defaults import *
from django.views.static import serve
import os

JAVASCRIPT_PATH = "%s/js" % os.path.dirname(__file__)

urlpatterns = patterns('ajax.views',
    (r'^(?P<application>\w+)/(?P<model>\w+).json', 'endpoint_loader'), 
    (r'^(?P<application>\w+)/(?P<model>\w+)/(?P<pk>\d+)/(?P<method>(update|delete|get|tags))/?(?P<taggit_command>(add|remove|set|clear|similar))?.json$', 'endpoint_loader'),
    (r'^js/(?P<path>.*)$', serve,
        {'document_root': JAVASCRIPT_PATH}),
)
