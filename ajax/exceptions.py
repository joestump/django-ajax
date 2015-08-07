from __future__ import absolute_import
import json

from django.utils.encoding import smart_str
from django.http import HttpResponse, HttpResponseNotFound, \
    HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseServerError, \
    HttpResponseBadRequest


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class PrimaryKeyMissing(Exception):
    pass


class AJAXError(Exception):
    RESPONSES = {
        400: HttpResponseBadRequest,
        403: HttpResponseForbidden,
        404: HttpResponseNotFound,
        405: HttpResponseNotAllowed,
        500: HttpResponseServerError,
    }

    def __init__(self, code, msg, **kwargs):
        self.code = code
        self.msg = msg
        self.extra = kwargs  # Any kwargs will be appended to the output.

    def get_response(self):
        try:
            msg = smart_str(self.msg.decode())
        except (AttributeError,):
            msg = smart_str(self.msg)
        error = {
            'success': False,
            'data': {
                'code': self.code,
                'message': msg
            }
        }
        error.update(self.extra)

        response = self.RESPONSES[self.code]()
        response.content = json.dumps(error, separators=(',', ':'))
        return response
