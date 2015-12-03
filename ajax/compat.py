from __future__ import absolute_import
import django

if django.VERSION >= (1, 7):
    from django.utils.module_loading import import_string as path_to_import
    from importlib import import_module
    from logging import getLogger
else:
    # 1.4 LTS compatibility
    from ajax.utils import import_by_path as path_to_import
    from django.utils.importlib import import_module
    from django.utils.log import getLogger
