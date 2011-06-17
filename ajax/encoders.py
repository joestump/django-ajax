from django.core import serializers
from ajax.exceptions import AlreadyRegistered, NotRegistered


class DefaultEncoder(object):
    def to_dict(self, record):
        data = serializers.serialize('python', [record])[0]
        ret = data['fields']
        ret['pk'] = data['pk']
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
