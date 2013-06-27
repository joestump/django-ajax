import base64
import hashlib
import random
from django.db import models
from django.contrib.auth import User


class ApiKey(models.Model):
    user = models.OneToOneField(User, related_name='api_key')
    key = models.CharField(max_length=40)

    def _generate_key():
        return base64.b64encode(hashlib.sha256(
            str(random.getrandbits(256))
        ).digest(), random.choice(
            ['rA', 'aZ', 'gQ', 'hH', 'hG', 'aR', 'DD']
        )).rstrip('==')

    def _unique_key(self):
        key = self._generate_key()
        while ApiKey.objects.filter(key=key).exists():
            key = self._generate_key()
        return key

    @classmethod
    def create(cls, user):
        key = cls._unique_key()
        api_key = cls(user=user, key=key)
        return api_key

    @classmethod
    def reset(cls, user):
        user.api_key.key = cls._unique_key()
        user.api_key.save()
        return user.api_key
