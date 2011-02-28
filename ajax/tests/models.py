from django.db import models
from django.contrib.admin.models import User

class Entry(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(User)
    category = models.ForeignKey('Category')

class Category(models.Model):
    name = models.CharField(max_length=100)
