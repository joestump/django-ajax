from ajax import endpoint
from ajax.decorators import login_required
from ajax.endpoints import ModelEndpoint
from ajax.exceptions import AJAXError
from example.models import Widget


@login_required
def echo(request):
    """For testing purposes only."""
    return request.POST


endpoint.register(Widget, ModelEndpoint)
