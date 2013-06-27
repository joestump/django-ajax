from django.contrib.auth import User


class BaseAuthentication(object):
    def is_authenticated(self, request, application, method):
        if request.user.is_authenticated():
            return True

        return False


class ApiKeyAuthentication(object):
    def get_user(self, username):
        try:
            return User.objects.get(username_field=username)
        except:
            return None

    def is_authenticated(self, request, application, method):
        if not request.META.get('HTTP_AUTHORIZATION'):
            return False
        (auth_type, data) = request.META['HTTP_AUTHORIZATION'].split()

        username, api_key = data.split(':', 1)

        user = self.get_user(username)

        if not user:
            return False

        if not user.api_key or user.api_key.key != api_key:
            return False

        return True
