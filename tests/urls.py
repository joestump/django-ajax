from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',
    url(r'^ajax/', include('ajax.urls')),
)
