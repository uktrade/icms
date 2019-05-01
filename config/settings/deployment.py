from .base import *
import environ

env = environ.Env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('ICMS_SECRET_KEY')
DEBUG = env.bool('ICMS_DEBUG', False)
ALLOWED_HOSTS = env.list('ICMS_ALLOWED_HOSTS')

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {'default': env.db('DATABASE_URL')}

# TODO compression causes 50 error on server
# STATICFILES_STORAGE='whitenoise.storage.CompressedManifestStaticFilesStorage'

#  Google recaptcha. Using test keys on localhost
RECAPTCHA_PUBLIC_KEY = env.str('ICMS_RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = env.str('ICMS_RECAPTCHA_PRIVATE_KEY')

# Email
EMAIL_API_KEY = env.str('ICMS_EMAIL_API_KEY')
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
            'level': 'INFO',
        }
    },
}
