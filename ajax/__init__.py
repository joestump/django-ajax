from django.core import serializers
from django.db import models
from django.utils import simplejson as json
from django.utils.encoding import smart_str
from django.db.models.fields import FieldDoesNotExist
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
    if not hasattr(args[0], 'pk') or args[0].pk == None:
        raise PrimaryKeyMissing()

    return func(*args, **kwargs)

class ModelEndpoint(object):
    def __init__(self, application, model, method, pk):
        self.application = application
        self.model = model
        self.method = method
        self.pk = pk

    def create(self, request):
        record = self.model(**self._extract_data(request))
        if self.can_create(request.user, record):
            record.save()
            return self._encode_record(record)
        else:
            return HttpResponseForbidden()

    @require_pk
    def update(self, request):
        record = self._get_record()
        if self.can_update(request.user, record):
            for key, val in self._extract_data(request).iteritems():
                setattr(record, key, val)

            record.save()
            return self._encode_record(record)
        else:
            return HttpResponseForbidden()

    @require_pk
    def delete(self, request):
        record = self._get_record()
        if self.can_delete(request.user, record):
            record.delete()
            return {'pk': int(self.pk)}
        else:
            return HttpResponseForbidden()

    @require_pk
    def get(self, request):
        record = self._get_record()
        if self.can_get(request.user, record):
            return self._encode_record(record)
        else:
            return HttpResponseForbidden()

    def _extract_data(self, request):
        """Extract data from POST.

        Handles extracting a vanilla Python dict of values that are present
        in the given model. This also handles instances of ``ForeignKey`` and
        will convert those to the appropriate object instances from the
        database. In other words, it will see that user is a ``ForeignKey`` to
        Django's ``User`` class, assume the value is an appropriate pk, and
        load up that record.
        """
        data = {}
        for field, val in request.POST.iteritems():
            try:
                f = self.model._meta.get_field(field)
                if isinstance(f, models.ForeignKey):
                    data[smart_str(field)] = f.rel.to.objects.get(pk=val)
                else:
                    data[smart_str(field)] = val
            except FieldDoesNotExist:
                pass

        return data

    def _encode_data(self, data):
        """Encode a ``QuerySet`` to a Python dict.

        Handles converting a ``QuerySet`` (or something that looks like one) to
        a more vanilla version of a list of dict's without the extra 
        inspection-related cruft.
        """
        data = serializers.serialize("python", data)
        ret = []
        for d in data:
            tmp = d['fields']
            tmp['pk'] = d['pk']
            ret.append(tmp)

        return ret

    def _encode_record(self, record):
        """Encode a record to a dict.

        This will take a Django model, encode it to a normal Python dict, and
        then inspect the data for instances of ``ForeignKey`` and convert 
        those to a dict of the related record.
        """
        data = self._encode_data([record])[0]
        for field, val in data.iteritems():
            try:
                f = self.model._meta.get_field(field)
                if isinstance(f, models.ForeignKey):
                    row = f.rel.to.objects.get(pk=val)
                    new_value = self._encode_record(row)
                elif isinstance(f, models.BooleanField):
                    # If someone could explain to me why the fuck the Python
                    # serializer appears to serialize BooleanField to a string
                    # with "True" or "False" in it, please let me know.
                    if val == "True":
                        new_value = True
                    else:
                        new_value = False
                else:
                    new_value = val

                data[smart_str(field)] = new_value
            except FieldDoesNotExist:
                pass

        return data

    def _get_record(self):
        """Fetch a given record.

        Handles fetching a record from the database along with throwing an
        appropriate instance of ``AJAXError`.
        """
        if not self.pk:
            raise AJAXError(400, _('Invalid request for record.'))

        try:
            return self.model.objects.get(pk=self.pk)
        except self.model.DoesNotExist:
            raise AJAXError(404, _('Record "%s" not found.') % self.pk)

    def can_get(self, user, record):
        return True

    def _user_is_active_or_staff(self, user, record):
        return ((user.is_authenticated() and user.is_active) or user.is_staff)

    can_create = _user_is_active_or_staff
    can_update = _user_is_active_or_staff
    can_delete = _user_is_active_or_staff

    def authenticate(self, request, application, method):
        """Authenticate the AJAX request.

        By default any request to fetch a model is allowed for any user, 
        including anonymous users. All other methods minimally require that
        the user is already logged in.

        Most likely you will want to lock down who can edit and delete various
        models. To do this, just override this method in your child class. 
        """
        if request.user.is_authenticated():
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

    def load(self, model_name, application, method, pk):
        for model in self._registry:
            if model.__name__.lower() == model_name:
                return self._registry[model](application, model, method, pk)

        raise NotRegistered()

endpoint = Endpoints()
