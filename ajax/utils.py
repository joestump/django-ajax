from __future__ import absolute_import
import sys

from django.core.exceptions import ImproperlyConfigured
from ajax.compat import import_module


def import_by_path(dotted_path, error_prefix=''):
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImproperlyConfigured if something goes
    wrong. This has come straight from Django 1.6
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        raise ImproperlyConfigured("%s%s doesn't look like a module path" % (
            error_prefix, dotted_path))
    try:
        module = import_module(module_path)
    except ImportError as e:
        raise ImproperlyConfigured('%sError importing module %s: "%s"' % (
            error_prefix, module_path, e))
    try:
        attr = getattr(module, class_name)
    except AttributeError:
        raise ImproperlyConfigured(
            '%sModule "%s" does not define a "%s" attribute/class' % (
                error_prefix, module_path, class_name
            )
        )
    return attr
