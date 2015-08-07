from __future__ import absolute_import
from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^ajax/', include('ajax.urls')),
)
