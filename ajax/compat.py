import django

if django.VERSION >= (1, 7):
    from django.utils.module_loading import import_string as path_to_import
elif django.VERSION >= (1, 6):
    from django.utils.module_loading import import_by_path as path_to_import
    path_to_import = import_by_path
else:
    from ajax.utils import import_by_path as path_to_import
