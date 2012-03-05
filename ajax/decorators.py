from django.utils.translation import ugettext as _
from decorator import decorator
from ajax.exceptions import AJAXError, PrimaryKeyMissing

@decorator
def login_required(f, *args, **kwargs):
    if not args[0].user.is_authenticated():
        raise AJAXError(403, _('User must be authenticated.'))

    return f(*args, **kwargs)


@decorator
def require_pk(func, *args, **kwargs):
    if not hasattr(args[0], 'pk') or args[0].pk is None:
        raise PrimaryKeyMissing()

    return func(*args, **kwargs)


@decorator
def json_response(f, *args, **kwargs):
    """Wrap a view in JSON.

    This decorator runs the given function and looks out for ajax.AJAXError's,
    which it encodes into a proper HttpResponse object. If an unknown error
    is thrown it's encoded as a 500.

    All errors are then packaged up with an appropriate Content-Type and a JSON
    body that you can inspect in JavaScript on the client. They look like:

    {
        "message": "Error message here.", 
        "code": 500
    }

    Please keep in mind that raw exception messages could very well be exposed
    to the client if a non-AJAXError is thrown.
    """ 
    try:
        result = f(*args, **kwargs)
        if isinstance(result, AJAXError):
            raise result
    except AJAXError, e:
        result = e.get_response()
    except Http404, e:
        result = AJAXError(404, e.__str__()).get_response()
    except Exception, e:
        if settings.DEBUG or \
            (args[0].user.is_authenticated() and args[0].user.is_superuser):
            import sys
            type, message, trace = sys.exc_info()
            import traceback 
            tb = [{'file': l[0], 'line': l[1], 'in': l[2], 'code': l[3]} for 
                l in traceback.extract_tb(trace)]
            result = AJAXError(500, message, traceback=tb).get_response()
        else:
            result = AJAXError(500, message).get_response()

    result['Content-Type'] = 'application/json'
    return result
