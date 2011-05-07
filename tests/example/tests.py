from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import simplejson as json


class BaseTest(TestCase):
    fixtures = ['users.json', 'widgets.json']

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

        return (response, json.loads(response.content))


class EndpointTests(BaseTest):
    def test_echo(self):
        """Test the ad-hoc echo endpoint."""
        resp, content = self.post('/ajax/example/echo.json',
            {'name': 'Joe Stump', 'age': 31})
        self.assertEquals('Joe Stump', content['name'])
        self.assertEquals('31', content['age'])

    def test_logged_out_user_fails(self):
        """Make sure @login_required rejects requests to echo."""
        self.client.logout()
        resp, content = self.post('/ajax/example/echo.json', {},
            status_code=403)
