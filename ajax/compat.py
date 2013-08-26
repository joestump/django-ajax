import django

if django.VERSION >= (1, 6):
    from django.utils.module_loading import import_by_path
    path_to_import = import_by_path
else:
    from ajax.utils import import_by_path
    path_to_import = import_by_path
