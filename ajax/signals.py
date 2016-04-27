from __future__ import absolute_import
import django.dispatch

ajax_created = django.dispatch.Signal(providing_args=['instance'])
ajax_deleted = django.dispatch.Signal(providing_args=['instance'])
ajax_updated = django.dispatch.Signal(providing_args=['instance'])
