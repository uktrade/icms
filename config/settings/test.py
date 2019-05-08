from .development import *  # NOQA
INSTALLED_APPS.remove('debug_toolbar')  # NOQA
MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')  # NOQA
