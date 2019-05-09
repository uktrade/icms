from .development import *  # NOQA
import environ

env = environ.Env()

INSTALLED_APPS.remove('debug_toolbar')  # NOQA
MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')  # NOQA

AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', 'test')
AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', 'test')
EMAIL_FROM = env.str('ICMS_EMAIL_FROM', 'test@example.com')
