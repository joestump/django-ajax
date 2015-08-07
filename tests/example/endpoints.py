from __future__ import absolute_import
from ajax import endpoint
from ajax.decorators import login_required
from ajax.endpoints import ModelEndpoint
from .models import Widget, Category


@login_required
def echo(request):
    """For testing purposes only."""
    return request.POST


class WidgetEndpoint(ModelEndpoint):
    model = Widget
    max_per_page = 100
    can_list = lambda *args, **kwargs: True

    def get_queryset(self, request):
        return Widget.objects.all()

class CategoryEndpoint(ModelEndpoint):
    model = Category


endpoint.register(Widget, WidgetEndpoint)
endpoint.register(Category, CategoryEndpoint)
