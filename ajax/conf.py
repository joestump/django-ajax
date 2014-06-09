from django.conf import settings
from appconf import AppConf


class AjaxAppConf(AppConf):
    AJAX_AUTHENTICATION = 'ajax.authentication.BaseAuthentication'
