from django.utils import simplejson as json
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

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def get_response(self):
        error = {
            'code': self.code,
            'message': smart_str(self.msg)
        }

        response = self.RESPONSES[self.code]()
        response.content = json.dumps(error, indent=4)
        return response

