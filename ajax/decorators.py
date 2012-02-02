from django.utils.translation import ugettext as _
from decorator import decorator
from ajax.exceptions import AJAXError, PrimaryKeyMissing
from functools import wraps
from django.utils.decorators import available_attrs

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


def allowed_methods(request_method_list=['get','post','update','create','list']):
    
    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def inner(request, *args, **kwargs):
            if request.method not in request_method_list:
                raise AJAXError(403, _('Access denied.'))
            return func(request, *args, **kwargs)
        return inner
    return decorator        
    