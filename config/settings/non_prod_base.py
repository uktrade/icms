from .base import *  # NOQA”
import environ

env = environ.Env()

ALLOWED_HOSTS = env.list('ICMS_ALLOWED_HOSTS', default=['localhost', 'web'])

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    'default': env.db('DATABASE_URL', 'postgres://postgres:password@db:5432/postgres')
}

#  Google recaptcha. Using test keys on localhost
RECAPTCHA_PUBLIC_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_PRIVATE_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# getAddress.io api key
ADDRESS_API_KEY = env.str('ICMS_ADDRESS_API_KEY', default='')

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
