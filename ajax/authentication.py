class BaseAuthentication(object):
    def is_authenticated(self, request, application, method):
        if request.user.is_authenticated():
            return True

        return False
