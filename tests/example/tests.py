from django.test import TestCase
from django.contrib.auth.models import User
import json
from .models import Widget
from .endpoints import WidgetEndpoint


class BaseTest(TestCase):
    fixtures = ['users.json', 'categories.json', 'widgets.json']

    def setUp(self):
        self.login('jstump')

    def login(self, username, password='testing'):
        user = User.objects.get(username=username)
        login_successful = self.client.login(username=user.username,
            password=password)
        self.assertTrue(login_successful)

    def post(self, uri, data={}, debug=False, status_code=200):
        """Send an AJAX request.

        This handles sending the AJAX request via the built-in Django test
        client and then decodes the response.

        ``status_code`` lets you define what you expect the status code
        to be which will be tested before returning the response object
        and the decoded JSON content.

        ``debug`` if set to True will spit out the response and content.
        """
        response = self.client.post(uri, data)
        if debug:
            print response.__class__.__name__
            print response

        self.assertEquals(status_code, response.status_code)

        return response, json.loads(response.content)


class EncodeTests(BaseTest):
    def test_encode(self):
        from ajax.encoders import encoder
        widget = Widget.objects.get(pk=1)
        self.assertEquals(widget.title,'Iorem lipsum color bit amit')
        encoded = encoder.encode(widget)
        for k in ('title','active','description'):
            self.assertEquals(encoded[k],getattr(widget,k))
        widgets = Widget.objects.all()
        all_encoded = encoder.encode(widgets)
        for encoded in all_encoded:
            widget = Widget.objects.get(pk=encoded['pk'])
            for k in ('title','active','description'):
                self.assertEquals(encoded[k],getattr(widget,k))
        

class EndpointTests(BaseTest):
    def test_echo(self):
        """Test the ad-hoc echo endpoint."""
        resp, content = self.post('/ajax/example/echo.json',
            {'name': 'Joe Stump', 'age': 31})
        self.assertEquals('Joe Stump', content['data']['name'])
        self.assertEquals('31', content['data']['age'])

    def test_empty_foreign_key(self):
        """Test that nullable ForeignKey fields can be set to null"""
        resp, content = self.post('/ajax/example/widget/3/update.json',
            {'category': ''})
        self.assertEquals(None, content['data']['category'])
        self.assertEquals(None, Widget.objects.get(pk=3).category)

    def test_false_foreign_key(self):
        """Test that nullable ForeignKey fields can be set to null by setting it to false"""
        resp, content = self.post('/ajax/example/widget/6/update.json',
            {'category': False})
        self.assertEquals(None, content['data']['category'])
        self.assertEquals(None, Widget.objects.get(pk=6).category)

    def test_logged_out_user_fails(self):
        """Make sure @login_required rejects requests to echo."""
        self.client.logout()
        resp, content = self.post('/ajax/example/echo.json', {},
            status_code=403)


class MockRequest(object):
    def __init__(self, **kwargs):
        self.POST = kwargs


class ModelEndpointTests(BaseTest):
    def setUp(self):
        self.list_endpoint = WidgetEndpoint('example', Widget, 'list')

    def test_list_returns_all_items(self):
        results = self.list_endpoint.list(MockRequest())
        self.assertEqual(len(results), Widget.objects.count())

    def test_list_obeys_endpoint_pagination_amount(self):
        self.list_endpoint.max_per_page = 1
        results = self.list_endpoint.list(MockRequest())
        self.assertEqual(len(results), 1)

    def test_out_of_range_returns_empty_list(self):
        results = self.list_endpoint.list(MockRequest(current_page=99))
        self.assertEqual(len(results), 0)

    def test_request_doesnt_override_max_per_page(self):
        self.list_endpoint.max_per_page = 1
        results = self.list_endpoint.list(MockRequest(items_per_page=2))
        self.assertEqual(len(results), 1)
