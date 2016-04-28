from __future__ import absolute_import
from django.conf import settings
from appconf import AppConf


class AjaxAppConf(AppConf):
    AJAX_AUTHENTICATION = 'ajax.authentication.BaseAuthentication'
