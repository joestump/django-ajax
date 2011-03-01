from django.conf.urls.defaults import *

#    (r'^(?P<application>\w+)/(?P<endpoint>[a-z_]+).json$', 'endpoint_loader'),
urlpatterns = patterns('ajax.views',
    (r'^(?P<application>\w+)/(?P<model>\w+).json', 'endpoint_loader'), 
    (r'^(?P<application>\w+)/(?P<model>\w+)/(?P<pk>\d+)/(?P<method>(update|delete|get)).json$', 'endpoint_loader'),
)
