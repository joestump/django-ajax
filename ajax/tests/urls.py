from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^ajax/', include('ajax.urls')),
)
