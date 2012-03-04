from debug_toolbar.middleware import DebugToolbarMiddleware, add_content_handler
from django.utils import simplejson as json
from django.core.serializers.json import DjangoJSONEncoder


class AJAXDebugToolbarJSONEncoder(DjangoJSONEncoder):
    pass


class AJAXDebugToolbarMiddleware(DebugToolbarMiddleware):
    """
    Replaces django-debug-toolbar's default DebugToolbarMiddleware.

    This middleware overrides the DebugToolbarMiddleware.process_response() to
    return the toolbar data in the AJAX response if the request was an AJAX
    request. This allows for debugging via the browser console using data from the
    django-debug-toolbar panels.

    Sadly, I couldn't easily just override the logic in DebugToolbarMiddleware so
    I had to copy process_response here.
    """
    def _append_json(self, response, toolbar):
        payload = json.loads(response.content)
        payload['debug_toolbar'] = toolbar.stats['sql']
        response.content = json.dumps(payload, indent=4,
            cls=AJAXDebugToolbarJSONEncoder)
        return response


add_content_handler('_append_json', ['application/json', 'text/javascript'])
