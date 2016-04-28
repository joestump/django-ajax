from __future__ import absolute_import
from django.core import serializers
from ajax.exceptions import AlreadyRegistered, NotRegistered
from django.db.models.fields import FieldDoesNotExist
from django.db import models
from django.conf import settings
from django.utils.html import escape
from django.db.models.query import QuerySet
from django.utils.encoding import smart_str
import collections
import six


# Used to change the field name for the Model's pk.
AJAX_PK_ATTR_NAME = getattr(settings, 'AJAX_PK_ATTR_NAME', 'pk')


def _fields_from_model(model):
    return [field.name for field in model.__class__._meta.fields]


class DefaultEncoder(object):
    _mapping = {
        'IntegerField': int,
        'PositiveIntegerField': int,
        'AutoField': int,
        'FloatField': float,
    }

    def to_dict(self, record, expand=False, html_escape=False, fields=None):
        self.html_escape = html_escape
        if hasattr(record, '__exclude__') and callable(record.__exclude__):
            try:
                exclude = record.__exclude__()
                if fields is None:
                    fields = _fields_from_model(record)
                fields = set(fields) - set(exclude)
            except TypeError:
                pass
        data = serializers.serialize('python', [record], fields=fields)[0]

        if hasattr(record, 'extra_fields'):
            ret = record.extra_fields
        else:
            ret = {}

        ret.update(data['fields'])
        ret[AJAX_PK_ATTR_NAME] = data['pk']

        for field, val in six.iteritems(ret):
            try:
                f = record.__class__._meta.get_field(field)
                if expand and isinstance(f, models.ForeignKey):
                    try:
                        row = f.rel.to.objects.get(pk=val)
                        new_value = self.to_dict(row, False)
                    except f.rel.to.DoesNotExist:
                        new_value = None  # Changed this to None from {} -G
                else:
                    new_value = self._encode_value(f, val)

                ret[smart_str(field)] = new_value
            except FieldDoesNotExist as e:
                pass  # Assume extra fields are already safe.
                  
        if expand and hasattr(record, 'tags') and \
          record.tags.__class__.__name__.endswith('TaggableManager'):
          # Looks like this model is using taggit.
          ret['tags'] = [{'name': self._escape(t.name), 
          'slug': self._escape(t.slug)} for t in record.tags.all()]
          
        return ret

    __call__ = to_dict

    def _encode_value(self, field, value):
        if value is None:
            return value # Leave all None's as-is as they encode fine.

        try:
            return self._mapping[field.__class__.__name__](value)
        except KeyError:
            if isinstance(field, models.ForeignKey):
                f = field.rel.to._meta.get_field(field.rel.field_name)
                return self._encode_value(f, value)
            elif isinstance(field, models.BooleanField):
                # If someone could explain to me why the fuck the Python
                # serializer appears to serialize BooleanField to a string
                # with "True" or "False" in it, please let me know.
                return (value == "True" or (type(value) == bool and value))

        return self._escape(value)

    def _escape(self, value):
        if self.html_escape:
            return escape(value)
        return value


class HTMLEscapeEncoder(DefaultEncoder):
    """Encodes all values using Django's HTML escape function."""
    def _escape(self, value):
        return escape(value)


class ExcludeEncoder(DefaultEncoder):
    def __init__(self, exclude):
        self.exclude = exclude

    def __call__(self, record, html_escape=False):
        fields = set(_fields_from_model(record)) - set(self.exclude)
        return self.to_dict(record, html_escape=html_escape, fields=fields)


class IncludeEncoder(DefaultEncoder):
    def __init__(self, include):
        self.include = include

    def __call__(self, record, html_escape=False):
        return self.to_dict(record, html_escape=html_escape, fields=self.include)


class Encoders(object):
    def __init__(self):
        self._registry = {}

    def register(self, model, encoder):
        if model in self._registry:
            raise AlreadyRegistered()

        self._registry[model] = encoder

    def unregister(self, model):
        if model not in self._registry:
            raise NotRegistered()

        del self._registry[model]
    
    def get_encoder_from_record(self, record):
        if isinstance(record, models.Model) and \
            record.__class__ in self._registry:
            encoder = self._registry[record.__class__]
        else:
            encoder = DefaultEncoder()
        return encoder
        
    def encode(self, record, encoder=None, html_escape=False):
        if isinstance(record, collections.Iterable):
            ret = []
            for i in record:
                if not encoder:
                    encoder = self.get_encoder_from_record(i)
                ret.append(self.encode(i, html_escape=html_escape))
        else:
            if not encoder:
                encoder = self.get_encoder_from_record(record)
            ret = encoder(record, html_escape=html_escape)

        return ret


encoder = Encoders()
