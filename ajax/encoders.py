from django.core import serializers
from django.utils.html import escape
from ajax.exceptions import AlreadyRegistered, NotRegistered
from django.db.models.fields import FieldDoesNotExist
from django.db import models
from django.utils.encoding import smart_str

def encode_data(data):
    """Encode a ``QuerySet`` to a Python dict.

    Handles converting a ``QuerySet`` (or something that looks like one) to
    a more vanilla version of a list of dict's without the extra
    inspection-related cruft.
    """
    ret = []
    for d in data:
        ret.append(encode_record(d))

    return ret

def encode_record(record, expand=True):
    """Encode a record to a dict.

    This will take a Django model, encode it to a normal Python dict, and
    then inspect the data for instances of ``ForeignKey`` and convert
    those to a dict of the related record.
    """
    data = encoder.encode(record)
    for field, val in data.iteritems():
        try:
            f = record.__class__._meta.get_field(field)
            if expand and isinstance(f, models.ForeignKey):
                try:
                    row = f.rel.to.objects.get(pk=val)
                    new_value = encode_record(row, False)
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
                new_value = val

            data[smart_str(field)] = new_value
        except FieldDoesNotExist:
            pass

    return data


class DefaultEncoder(object):
    def to_dict(self, record):
        data = serializers.serialize('python', [record])[0]


        if hasattr(record, 'extra_fields'):
            ret = record.extra_fields
        else:
            ret = {}
            
        ret.update(data['fields'])
        ret['pk'] = data['pk']

        for key, val in ret.iteritems():
            ret[key] = escape(val)

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
        if record.__class__ in self._registry:
            encoder = self._registry[record.__class__]
        else:
            encoder = DefaultEncoder() 

        return encoder(record)


encoder = Encoders()
