from __future__ import absolute_import
import django
try:
    from django.conf.urls import patterns, include, url
except ImportError:
    from django.conf.urls import include, url

if django.VERSION < (1, 8):
    urlpatterns = patterns('',
        url(r'^ajax/', include('ajax.urls')),
    )
else:
    urlpatterns = [
        url(r'^ajax/', include('ajax.urls'))
    ]
