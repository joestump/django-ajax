import os

settings_file = '%s/settings.py' % os.path.dirname(__file__)
os.putenv('DJANGO_SETTINGS_MODULE', settings_file)
