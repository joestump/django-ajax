from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import simplejson as json
from models import Entry, Category
import sys
import os

class AJAXViewTests(TestCase):
    CATEGORY = 'My Category'
    urls = 'ajax.tests.urls'

    def setUp(self):
        password = 'tester_password'
        user = User.objects.create_user('tester', 'tester@example.com', 
            password)
        user.save() 
        login_successful = self.client.login(username=user.username,
            password=password)
        self.assertTrue(login_successful)

    def tearDown(self):
        user = User.objects.get(username='tester')
        user.delete()

    def test_echo_endpoint(self):
        result = self.client.post('/ajax/tests/echo.json', 
            {'foo': 'bar'})
        self.assertEquals(result.status_code, 200)
        data = json.loads(result.content)
        self.assertEquals(data['foo'], 'bar')

    def test_model_create(self):
        result = self.client.post('/ajax/tests/category/create.json', {
            'name': self.CATEGORY})
        self.assertEquals(result.status_code, 200)

    def test_model_delete(self):
        result = self.client.post('/ajax/tests/category/delete.json', {
            'pk': 1})
        self.assertEquals(result.status_code, 200) 
        try:
            c = Category.objects.get(pk=1)
            self.fail('Category still exists.')
        except Category.DoesNotExist:
            pass
