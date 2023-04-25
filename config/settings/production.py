# flake8: noqa: F405
from web.utils.sentry import init_sentry

from .base import *

SECRET_KEY = env.str("ICMS_SECRET_KEY")
DATABASES = {"default": env.db("DATABASE_URL")}
ALLOWED_HOSTS = env.list("ICMS_ALLOWED_HOSTS")

# TODO compression causes 50 error on server
# STATICFILES_STORAGE='whitenoise.storage.CompressedManifestStaticFilesStorage'

# Elastic APM config
INSTALLED_APPS += [  # NOQA
    "elasticapm.contrib.django",
    "django_audit_log_middleware",
]

MIDDLEWARE += [  # NOQA
    "django_audit_log_middleware.AuditLogMiddleware",
]

# Audit log middleware user field
AUDIT_LOG_USER_FIELD = "username"

ELASTIC_APM = {
    "SERVICE_NAME": "ICMS",
    "SECRET_TOKEN": env.str("ELASTIC_APM_SECRET_TOKEN"),
    "SERVER_URL": env.str("ELASTIC_APM_URL"),
    "ENVIRONMENT": env.str("ELASTIC_APM_ENVIRONMENT", default="development"),
    "SERVER_TIMEOUT": env.str("ELASTIC_APM_SERVER_TIMEOUT", default="20s"),
}

init_sentry()
