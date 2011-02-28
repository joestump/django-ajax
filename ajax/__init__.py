from django.forms.models import model_to_dict
from django.utils import simplejson as json
from django.http import HttpResponse, HttpResponseNotFound, \
    HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseServerError, \
    HttpResponseBadRequest
from decorator import decorator 

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
            'message': self.msg
        }

        response = self.RESPONSES[self.code]()
        response.content = json.dumps(error, indent=4)
        return response

@decorator
def require_pk(func, *args, **kwargs):
    if 'pk' not in args[0].request.POST:
        raise PrimaryKeyMissing()

class ModelEndpoint(object):
    def __init__(self, model, request):
        self.model = model
        self.request = request

    def create(self):
        record = self.model(**self._extract_data())
        if self.can_create(self.request.user):
            record.save()
            return {'pk': record.pk}
        else:
            return HttpResponseForbidden()

    @require_pk
    def update(self):
        record = self.model(pk=self.request.POST['pk'])
        if self.can_edit(self.request.user, record):
            data = self._extract_data()
            return model_to_dict(record)
        else:
            return HttpResponseForbidden()

    @require_pk
    def delete(self):
        record = self.model(pk=self.request.POST['pk'])
        if self.can_edit(self.request.user, record):
            record.delete()
            return {'pk': self.request.POST['pk']}
        else:
            return HttpResponseForbidden()

    @require_pk
    def get(self):
        record = self.model(pk=self.request.POST['pk'])
        if self.can_read(self.request.user, record):
            return model_to_dict(record)
        else:
            return HttpResponseForbidden()

    def _extract_data(self):
        data = {}
        for field, val in self.request.POST.iteritems():
            if hasattr(self.model, field):
                data[field] = val

        return data       

    def can_edit(self, user, record):
        return True

    def can_read(self, user, record):
        return True

    def can_create(self, user):
        return True

    def authenticate(self, method):
        """Authenticate the AJAX request.

        By default any request to fetch a model is allowed for any user, 
        including anonymous users. All other methods minimally require that
        the user is already logged in.

        Most likely you will want to lock down who can edit and delete various
        models. To do this, just override this method in your child class. 
        """

        if method == "get":
            return True

        if self.request.user.is_authenticated():
            return True
            
        return False

class Endpoints(object):
    def __init__(self):
        self._registry = {}

    def register(self, model, endpoint):
        if model in self._registry:
            raise AlreadyRegistered()

        self._registry[model] = endpoint

    def unregister(self, model):
        if model not in self._registry:
            raise NotRegistered()        

        del self._registry[model]

    def load(self, model_name, request):
        for model in self._registry:
            if model.__name__.lower() == model_name:
                return self._registry[model](model, request)

        raise NotRegistered()

endpoint = Endpoints()
