from .development import *  # NOQA

INSTALLED_APPS = [
    'django_smoke_tests',
] + INSTALLED_APPS  # NOQA

SKIP_SMOKE_TESTS = ('access-flow', 'request-access', 'admin')
