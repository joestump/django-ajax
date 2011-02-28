from django.conf.urls.defaults import *

urlpatterns = patterns('ajax.views',
    (r'^(?P<application>\w+)/(?P<endpoint>[a-z_]+).json$', 'endpoint_loader'),
    (r'^(?P<application>\w+)/(?P<model>\w+)/(?P<method>(create|update|delete|get)).json$', 'model_loader'),
)
