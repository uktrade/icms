from .base import *
import environ
from django.core.management.utils import get_random_secret_key

env = environ.Env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('ICMS_SECRET_KEY', default=get_random_secret_key())
DEBUG = env.bool('ICMS_DEBUG', True)
ALLOWED_HOSTS = env.list('ICMS_ALLOWED_HOSTS', default=['localhost'])

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL', 'postgres://postgres@db:5432/postgres')
}

#  Google recaptcha. Using test keys on localhost
RECAPTCHA_PUBLIC_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_PRIVATE_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# Email
EMAIL_API_KEY = env.str('ICMS_EMAIL_API_KEY', '')
EMAIL_REPLY_TO_ID = env.str('ICMS_EMAIL_REPLY_TO_ID', None)

# Loging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':
            '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} - {message} [{module}]',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'web': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    },
}
