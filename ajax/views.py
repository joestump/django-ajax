from django.http import HttpResponse
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from decorator import decorator
import ajax


@decorator
def ajax_response(f, *args, **kwargs):
    try:
        result = f(*args, **kwargs)
    except ajax.AJAXError, e:
        result = e.get_response()
    except Exception, e:
        result = ajax.AJAXError(500, str(e)).get_response()

    result['Content-Type'] = 'application/json'
    return result


@ajax_response
def endpoint_loader(request, application, endpoint):
    try:
        module = __import__('%s.endpoints' % application, globals(), 
            locals(), [endpoint], -1)
        try:
            func = getattr(module, endpoint)
        except AttributeError:
            raise ajax.AJAXError(404, 
                _('AJAX endpoint %s is invalid' % endpoint))

        data = func(request)
        if isinstance(data, HttpResponse):
            return data
        else:
            return HttpResponse(json.dumps(data, indent=4))
    except ImportError:
        raise ajax.AJAXError(404, _('AJAX endpoint is invalid.'))


@ajax_response
def model_loader(request, application, model, method):
    try:
        # Dry import the endpoints.py file for the application as that is
        # where the endpoint class definitions should be and where they are
        # very likely to be registered with us.
        module = __import__('%s.endpoints' % application, globals(), 
            locals(), [], -1)

        endpoint = ajax.endpoint.load(model, request)
        if endpoint.authenticate(method.lower()):
            data = endpoint.__getattribute__(method.lower())() 
            if isinstance(data, HttpResponse):
                return data 
            else:
                return HttpResponse(json.dumps(data, indent=4))
        else:
            raise ajax.AJAXError(403, _('User is not authorized.'))
    except ajax.NotRegistered:
        raise ajax.AJAXError(500, _('Invalid model.'))
