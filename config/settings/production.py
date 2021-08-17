import environ
import structlog

from web.utils.sentry import init_sentry

from .base import *  # NOQA

env = environ.Env()

VCAP_SERVICES = env.json("VCAP_SERVICES")

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

# Email/phone contacts
EMAIL_FROM = env.str("ICMS_EMAIL_FROM")
ILB_CONTACT_EMAIL = env.str("ICMS_ILB_CONTACT_EMAIL")
ILB_GSI_CONTACT_EMAIL = env.str("ICMS_ILB_GSI_CONTACT_EMAIL")
ILB_CONTACT_PHONE = env.str("ICMS_ILB_CONTACT_PHONE")
ICMS_FIREARMS_HOMEOFFICE_EMAIL = env.str("ICMS_FIREARMS_HOMEOFFICE_EMAIL")
ICMS_CFS_HSE_EMAIL = env.str("ICMS_CFS_HSE_EMAIL")
ICMS_GMP_BEIS_EMAIL = env.str("ICMS_GMP_BEIS_EMAIL")

# for https://github.com/uktrade/django-chunk-s3-av-upload-handlers
app_bucket_creds = VCAP_SERVICES["aws-s3-bucket"][0]["credentials"]
AWS_REGION = app_bucket_creds["aws_region"]
AWS_ACCESS_KEY_ID = app_bucket_creds["aws_access_key_id"]
AWS_SECRET_ACCESS_KEY = app_bucket_creds["aws_secret_access_key"]
AWS_STORAGE_BUCKET_NAME = app_bucket_creds["bucket_name"]

# getAddress.io api key
ADDRESS_API_KEY = env.str("ICMS_ADDRESS_API_KEY")

WSGI_APPLICATION = "config.wsgi.application"

# Elastic APM config
INSTALLED_APPS += [  # NOQA
    "elasticapm",
    "django_audit_log_middleware",
]

MIDDLEWARE += [  # NOQA
    "django_audit_log_middleware.AuditLogMiddleware",
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
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "web": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

init_sentry()

# minifi html (djano-htmlmin)
HTML_MINIFY = True

# Audit log middleware user field
AUDIT_LOG_USER_FIELD = "username"
