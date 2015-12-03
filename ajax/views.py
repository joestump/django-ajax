from __future__ import absolute_import

import json
from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from ajax.compat import getLogger
from django.core.serializers.json import DjangoJSONEncoder
from ajax.exceptions import AJAXError, NotRegistered
from ajax.decorators import json_response
from ajax.compat import import_module
import ajax


logger = getLogger('django.request')


class EnvelopedResponse(object):
    """
    Object used to contain metadata about the request that will be added to
    the wrapping json structure (aka the envelope).

    :param: data - The object representation that you want to return
    :param: metadata - dict of information which will be merged with the
                       envelope.
    """
    def __init__(self, data, metadata):
        self.data = data
        self.metadata = metadata

@json_response
def endpoint_loader(request, application, model, **kwargs):
    """Load an AJAX endpoint.

    This will load either an ad-hoc endpoint or it will load up a model
    endpoint depending on what it finds. It first attempts to load ``model``
    as if it were an ad-hoc endpoint. Alternatively, it will attempt to see if
    there is a ``ModelEndpoint`` for the given ``model``.
    """
    if request.method != "POST":
        raise AJAXError(400, _('Invalid HTTP method used.'))

    try:
        module = import_module('%s.endpoints' % application)
    except ImportError as e:
        if settings.DEBUG:
            raise e
        else:
            raise AJAXError(404, _('AJAX endpoint does not exist.'))

    if hasattr(module, model):
        # This is an ad-hoc endpoint
        endpoint = getattr(module, model)
    else:
        # This is a model endpoint
        method = kwargs.get('method', 'create').lower()
        try:
            del kwargs['method']
        except:
            pass

        try:
            model_endpoint = ajax.endpoint.load(model, application, method,
                **kwargs)
            if not model_endpoint.authenticate(request, application, method):
                raise AJAXError(403, _('User is not authorized.'))

            endpoint = getattr(model_endpoint, method, False)

            if not endpoint:
                raise AJAXError(404, _('Invalid method.'))
        except NotRegistered:
            raise AJAXError(500, _('Invalid model.'))

    data = endpoint(request)
    if isinstance(data, HttpResponse):
        return data

    if isinstance(data, EnvelopedResponse):
        envelope = data.metadata
        payload = data.data
    else:
        envelope = {}
        payload = data

    envelope.update({
        'success': True,
        'data': payload,
    })

    return HttpResponse(json.dumps(envelope, cls=DjangoJSONEncoder,
        separators=(',', ':')))
