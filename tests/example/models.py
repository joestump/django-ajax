from django.db import models


class Widget(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200, null=True, blank=True)
    active = models.BooleanField()
