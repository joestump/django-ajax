from django.core import serializers
from django.utils.html import escape
from ajax.exceptions import AlreadyRegistered, NotRegistered
from django.db.models.fields import FieldDoesNotExist
from django.db import models
from django.db.models.query import QuerySet
from django.utils.encoding import smart_str
import collections


class DefaultEncoder(object):
    def to_dict(self, record, expand=True):
        data = serializers.serialize('python', [record])[0]

        if hasattr(record, 'extra_fields'):
            ret = record.extra_fields
        else:
            ret = {}
            
        ret.update(data['fields'])
        ret['pk'] = data['pk']

        for field, val in ret.iteritems():
            try:
                f = record.__class__._meta.get_field(field)
                if expand and isinstance(f, models.ForeignKey):
                    try:
                        row = f.rel.to.objects.get(pk=val)
                        new_value = self.to_dict(row, False)
                    except f.rel.to.DoesNotExist:
                        new_value = None  # Changed this to None from {} -G
                elif isinstance(f, models.BooleanField):
                    # If someone could explain to me why the fuck the Python
                    # serializer appears to serialize BooleanField to a string
                    # with "True" or "False" in it, please let me know.
                    if val == "True" or (type(val) == bool and val):
                        new_value = True
                    else:
                        new_value = False
                else:
                    new_value = escape(val)
    
                ret[smart_str(field)] = new_value
            except FieldDoesNotExist, e:
                pass

        return ret

    __call__ = to_dict


class ExcludeEncoder(DefaultEncoder):
    def __init__(self, exclude):
        self.exclude = exclude

    def __call__(self, record):
        data = self.to_dict(record)
        final = {}
        for key, val in data.iteritems():
            if key in self.exclude:
                continue

            final[key] = val

        return final


class IncludeEncoder(DefaultEncoder):
    def __init__(self, include):
        self.include = include

    def __call__(self, record):
        data = self.to_dict(record)
        final = {}
        for key, val in data.iteritems():
            if key not in self.include:
                continue
    
            final[key] = val

        return final


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

    def encode(self, record):
        if isinstance(record, models.Model) and \
            record.__class__ in self._registry:
            encoder = self._registry[record.__class__]
        else:
            encoder = DefaultEncoder() 

        if isinstance(record, collections.Iterable):
            ret = []
            for i in record:
                ret.append(self.encode(i))
        else:
            ret = encoder(record)

        return ret


encoder = Encoders()
