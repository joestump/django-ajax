from ajax import endpoint
from ajax.decorators import login_required
from ajax.endpoints import ModelEndpoint
from ajax.exceptions import AJAXError


@login_required
def echo(request):
    """For testing purposes only."""
    return request.POST


class WidgetEndpoint(ajax.endpoints.ModelEndpoint):
    pass

ajax.endpoint.register(Category, CategoryEndpoint)
