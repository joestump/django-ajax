from __future__ import absolute_import
import json

from django.utils import six
from debug_toolbar.middleware import DebugToolbarMiddleware, add_content_handler
from django.core.serializers.json import DjangoJSONEncoder


class AJAXDebugToolbarJSONEncoder(DjangoJSONEncoder):
    pass


class AJAXDebugToolbarMiddleware(DebugToolbarMiddleware):
    """
    Replaces django-debug-toolbar's default DebugToolbarMiddleware.

    This middleware overrides the DebugToolbarMiddleware.process_response() to
    return the toolbar data in the AJAX response if the request was an AJAX
    request. This allows for debugging via the browser console using data from 
    the django-debug-toolbar panels.
    """
    def _append_json(self, response, toolbar):
        if isinstance(response.content, six.text_type):
            payload = json.loads(response.content)
        else:
            payload = json.loads(response.content.decode('utf-8'))
        payload['debug_toolbar'] = {
            'sql': toolbar.stats['sql'],
            'timer': toolbar.stats['timer']
        }
        try:
            response.content = json.dumps(payload, indent=4,
                cls=AJAXDebugToolbarJSONEncoder)
        except:
            pass
        return response


add_content_handler('_append_json', ['application/json', 'text/javascript'])
