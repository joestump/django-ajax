from ajax import endpoint
from ajax.decorators import login_required
from ajax.endpoints import ModelEndpoint
from .models import Widget


@login_required
def echo(request):
    """For testing purposes only."""
    return request.POST


class WidgetEndpoint(ModelEndpoint):
    model = Widget
    max_per_page = 100

endpoint.register(Widget, WidgetEndpoint)
