from .non_prod_base import *  # NOQA
import environ

env = environ.Env()

SECRET_KEY = env.str('ICMS_SECRET_KEY', default='test')

# Email
AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', 'test')
AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', 'test')
EMAIL_FROM = env.str('ICMS_EMAIL_FROM', 'test@example.com')
