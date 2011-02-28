import ajax
print ajax.__file__
from models import Category, Entry

def echo(request):
    return request.POST

class CategoryEndpoint(ajax.ModelEndpoint):
    pass

ajax.endpoint.register(Category, CategoryEndpoint)
