from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import simplejson as json
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import FieldDoesNotExist
from ajax.decorators import require_pk
from ajax.exceptions import AJAXError, AlreadyRegistered, NotRegistered, \
    PrimaryKeyMissing


class BaseEndpoint(object):
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

    def _encode_record(self, record, expand=True):
        """Encode a record to a dict.

        This will take a Django model, encode it to a normal Python dict, and
        then inspect the data for instances of ``ForeignKey`` and convert
        those to a dict of the related record.
        """
        data = self._encode_data([record])[0]
        for field, val in data.iteritems():
            try:
                f = record.__class__._meta.get_field(field)
                if expand and isinstance(f, models.ForeignKey):
                    try:
                        row = f.rel.to.objects.get(pk=val)
                        new_value = self._encode_record(row, False)
                    except f.rel.to.DoesNotExist:
                        new_value = None  # Changed this to None from {} -G
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


class BaseModelFormEndpoint(BaseEndpoint):
    def __init__(self, application, model, method, pk):
        self.application = application
        self.model = model
        self.method = method
        self.pk = pk


class ModelEndpoint(BaseModelFormEndpoint):
    _value_map = {
        'false': False,
        'true': True,
        'null': None
    }

    def create(self, request):
        record = self.model(**self._extract_data(request))
        if self.can_create(request.user, record):
            return self._encode_record(self._save(record))
        else:
            raise AJAXError(403, _("Access to endpoint is forbidden"))

    def _save(self, record):
        try:
            record.full_clean()
            record.save()
            return record
        except ValidationError, e:
            raise AJAXError(400, _("Could not save model."),
                errors=e.message_dict)

    @require_pk
    def update(self, request):
        record = self._get_record()
        if self.can_update(request.user, record):
            for key, val in self._extract_data(request).iteritems():
                setattr(record, key, val)

            return self._encode_record(self._save(record))
        else:
            raise AJAXError(403, _("Access to endpoint is forbidden"))

    @require_pk
    def delete(self, request):
        record = self._get_record()
        if self.can_delete(request.user, record):
            record.delete()
            return {'pk': int(self.pk)}
        else:
            raise AJAXError(403, _("Access to endpoint is forbidden"))

    @require_pk
    def get(self, request):
        record = self._get_record()
        if self.can_get(request.user, record):
            return self._encode_record(record)
        else:
            raise AJAXError(403, _("Access to endpoint is forbidden"))

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
                val = self._extract_value(val)
                if val and isinstance(f, models.ForeignKey):
                    data[smart_str(field)] = f.rel.to.objects.get(pk=val)
                else:
                    data[smart_str(field)] = val
            except FieldDoesNotExist:
                pass

        return data

    def _extract_value(self, value):
        """If the value is true/false/null replace with Python equivalent."""
        return ModelEndpoint._value_map.get(smart_str(value).lower(), value)

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
            raise AJAXError(404, _('%s with id of "%s" not found.') % (
                self.model.__name__, self.pk))

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


class FormEndpoint(BaseModelFormEndpoint):
    """AJAX endpoint for processing Django forms.

    The models and forms are processed in pretty much the same manner, only a
    form class is used rather than a model class.
    """
    def create(self, request):
        form = self.model(request.POST)
        if form.is_valid():
            model = form.save()
            if hasattr(model, 'save'):
                # This is a model form so we save it and return the model.
                model.save()
                return self._encode_record(model)
            else:
                return model  # Assume this is a dict to encode.
        else:
            return self._encode_data(form.errors)

    def update(self, request):
        raise AJAXError(404, _("Endpoint does not exist."))

    delete = update
    get = update


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
