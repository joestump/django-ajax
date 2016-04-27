from __future__ import absolute_import
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _

from ajax.compat import path_to_import
from ajax.conf import settings
from ajax.decorators import require_pk
from ajax.exceptions import AJAXError, AlreadyRegistered, NotRegistered
from ajax.encoders import encoder
from ajax.signals import ajax_created, ajax_deleted, ajax_updated
from ajax.views import EnvelopedResponse
import six

try:
    from taggit.utils import parse_tags
except ImportError:
    def parse_tags(tagstring):
        raise AJAXError(500, 'Taggit required: http://bit.ly/RE0dr9')


class EmptyPageResult(object):
    def __init__(self):
        self.object_list = []


class ModelEndpoint(object):
    _value_map = {
        'false': False,
        'true': True,
        'null': None
    }

    immutable_fields = []  # List of model fields that are not writable.

    authentication = path_to_import(settings.AJAX_AUTHENTICATION)()

    def __init__(self, application, model, method, **kwargs):
        self.application = application
        self.model = model
        self.fields = [f.name for f in self.model._meta.fields]
        self.method = method
        self.pk = kwargs.get('pk', None)
        self.options = kwargs

    def create(self, request):
        record = self.model(**self._extract_data(request))
        if self.can_create(request.user, record):
            record = self._save(record)
            try:
                tags = self._extract_tags(request)
                record.tags.set(*tags)
            except KeyError:
                pass

            ajax_created.send(sender=record.__class__, instance=record)
            return encoder.encode(record)
        else:
            raise AJAXError(403, _("Access to endpoint is forbidden"))

    def tags(self, request):
        cmd = self.options.get('taggit_command', None)
        if not cmd:
            raise AJAXError(400, _("Invalid or missing taggit command."))

        record = self._get_record()
        if cmd == 'similar':
            result = record.tags.similar_objects()
        else:
            try:
                tags = self._extract_tags(request)
                getattr(record.tags, cmd)(*tags)
            except KeyError:
                pass  # No tags to set/manipulate in this request.
            result = record.tags.all()

        return encoder.encode(result)

    def get_queryset(self, request, **kwargs):
        return self.model.objects.none()

    def list(self, request):
        """
        List objects of a model. By default will show page 1 with 20 objects on it.

        **Usage**::

            params = {"items_per_page":10,"page":2} //all params are optional
            $.post("/ajax/{app}/{model}/list.json"),params)

        """

        max_items_per_page = getattr(self, 'max_per_page',
                                      getattr(settings, 'AJAX_MAX_PER_PAGE', 100))
        requested_items_per_page = request.POST.get("items_per_page", 20)
        items_per_page = min(max_items_per_page, requested_items_per_page)
        current_page = request.POST.get("current_page", 1)

        if not self.can_list(request.user):
            raise AJAXError(403, _("Access to this endpoint is forbidden"))

        objects = self.get_queryset(request)

        paginator = Paginator(objects, items_per_page)

        try:
            page = paginator.page(current_page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), return empty list.
            page = EmptyPageResult()

        data = [encoder.encode(record) for record in page.object_list]
        return EnvelopedResponse(data=data, metadata={'total': paginator.count})


    def _set_tags(self, request, record):
        tags = self._extract_tags(request)
        if tags:
            record.tags.set(*tags)

    def _save(self, record):
        try:
            record.full_clean()
            record.save()
            return record
        except ValidationError as e:
            raise AJAXError(400, _("Could not save model."),
                errors=e.message_dict)

    @require_pk
    def update(self, request):
        record = self._get_record()
        modified = self._get_record()

        update_record = False
        for key, val in six.iteritems(self._extract_data(request)):

            # Only setattr and save the model when a change has happened.
            if val != getattr(record, key):
                setattr(modified, key, val)
                update_record = True
 
        if self.can_update(request.user, record, modified=modified):
 
            if update_record:
                self._save(modified)

            try:
                tags = self._extract_tags(request)
                if tags:
                    modified.tags.set(*tags)
                else:
                    # If tags were in the request and set to nothing, we will
                    # clear them all out.
                    modified.tags.clear()
            except KeyError:
                pass

            ajax_updated.send(sender=record.__class__, instance=record)
            return encoder.encode(modified)
        else:
            raise AJAXError(403, _("Access to endpoint is forbidden"))

    @require_pk
    def delete(self, request):
        record = self._get_record()
        if self.can_delete(request.user, record):
            payload = {'pk': int(self.pk)}
            record.delete()
            ajax_deleted.send(sender=record.__class__, instance=record, payload=payload)
            return payload
        else:
            raise AJAXError(403, _("Access to endpoint is forbidden"))

    @require_pk
    def get(self, request):
        record = self._get_record()
        if self.can_get(request.user, record):
            return encoder.encode(record)
        else:
            raise AJAXError(403, _("Access to endpoint is forbidden"))

    def _extract_tags(self, request):
        # We let this throw a KeyError so that calling functions will know if
        # there were NO tags in the request or if there were, but that the
        # call had an empty tags list in it.
        raw_tags = request.POST['tags']
        tags = []
        if raw_tags:
            try:
                tags = [t for t in parse_tags(raw_tags) if len(t)]
            except Exception as e:
                pass

        return tags

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
        for field, val in six.iteritems(request.POST):
            if field in self.immutable_fields:
                continue  # Ignore immutable fields silently.

            if field in self.fields:
                field_obj = self.model._meta.get_field(field)
                val = self._extract_value(val)
                if isinstance(field_obj, models.ForeignKey):
                    if field_obj.null and not val:
                        clean_value = None
                    else:
                        clean_value = field_obj.rel.to.objects.get(pk=val)
                else:
                    clean_value = field_obj.to_python(val)
                data[smart_str(field)] = clean_value

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

    def _user_is_active_or_staff(self, user, record, **kwargs):
        return ((user.is_authenticated() and user.is_active) or user.is_staff)

    can_create = _user_is_active_or_staff
    can_update = _user_is_active_or_staff
    can_delete = _user_is_active_or_staff
    can_list = lambda *args, **kwargs: False

    def authenticate(self, request, application, method):
        """Authenticate the AJAX request.

        By default any request to fetch a model is allowed for any user,
        including anonymous users. All other methods minimally require that
        the user is already logged in.

        Most likely you will want to lock down who can edit and delete various
        models. To do this, just override this method in your child class.
        """
        return self.authentication.is_authenticated(request, application, method)


class FormEndpoint(object):
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
                return encoder.encode(model)
            else:
                return model  # Assume this is a dict to encode.
        else:
            return encoder.encode(form.errors)

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

    def load(self, model_name, application, method, **kwargs):
        for model in self._registry:
            if model.__name__.lower() == model_name:
                return self._registry[model](application, model, method,
                    **kwargs)

        raise NotRegistered()
