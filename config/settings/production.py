import environ
import os
import structlog

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # NOQA


env = environ.Env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("ICMS_SECRET_KEY")
DEBUG = env.bool("ICMS_DEBUG", False)
ALLOWED_HOSTS = env.list("ICMS_ALLOWED_HOSTS")

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL")}

# TODO compression causes 50 error on server
# STATICFILES_STORAGE='whitenoise.storage.CompressedManifestStaticFilesStorage'

#  Google recaptcha. Using test keys on localhost
RECAPTCHA_PUBLIC_KEY = env.str("ICMS_RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = env.str("ICMS_RECAPTCHA_PRIVATE_KEY")
SILENCED_SYSTEM_CHECKS = env.list("ICMS_SILENCED_SYSTEM_CHECKS", default=[])

# Email
AWS_SES_ACCESS_KEY_ID = env.str("AWS_SES_ACCESS_KEY_ID")
AWS_SES_SECRET_ACCESS_KEY = env.str("AWS_SES_SECRET_ACCESS_KEY")
EMAIL_FROM = env.str("ICMS_EMAIL_FROM")
ILB_CONTACT_EMAIL = env.str("ICMS_ILB_CONTACT_EMAIL")
ILB_CONTACT_PHONE = env.str("ICMS_ILB_CONTACT_PHONE")

# getAddress.io api key
ADDRESS_API_KEY = env.str("ICMS_ADDRESS_API_KEY")

WSGI_APPLICATION = "config.wsgi.application"

# Elastic APM config
INSTALLED_APPS += [  # NOQA
    "elasticapm.contrib.django",
]

ELASTIC_APM = {
    "SERVICE_NAME": "ICMS",
    "SECRET_TOKEN": env.str("ELASTIC_APM_SECRET_TOKEN"),
    "SERVER_URL": env.str("ELASTIC_APM_URL"),
    "ENVIRONMENT": env.str("ELASTIC_APM_ENVIRONMENT", default="development"),
    "SERVER_TIMEOUT": env.str("ELASTIC_APM_SERVER_TIMEOUT", default="20s"),
}

# Django Compressor
COMPRESS_OFFLINE = True

# Print json formatted logs to console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json_formatter",},},
    "loggers": {
        "django": {"handlers": ["console"], "level": "ERROR",},
        "web": {"handlers": ["console"], "level": "INFO",},
    },
}

sentry_sdk.init(
    os.environ.get("SENTRY_DSN"),
    environment=os.environ.get("SENTRY_ENVIRONMENT"),
    integrations=[DjangoIntegration()],
)

# minifi html (djano-htmlmin)
HTML_MINIFY = True
