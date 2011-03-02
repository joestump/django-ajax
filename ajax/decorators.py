from django.utils.translation import ugettext as _
from decorator import decorator
from ajax import AJAXError

@decorator
def login_required(f, *args, **kwargs):
    if not args[0].user.is_authenticated():
        raise AJAXError(403, _('User must be authenticated.'))

    return f(*args, **kwargs)
