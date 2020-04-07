from .non_prod_base import *  # NOQA
import environ

env = environ.Env()

SECRET_KEY = env.str('ICMS_SECRET_KEY', default='test')

# Email
AWS_SES_ACCESS_KEY_ID = env.str('AWS_SES_ACCESS_KEY_ID', 'test')
AWS_SES_SECRET_ACCESS_KEY = env.str('AWS_SES_SECRET_ACCESS_KEY', 'test')
EMAIL_FROM = env.str('ICMS_EMAIL_FROM', 'test@example.com')

CELERY_TASK_ALWAYS_EAGER = True
