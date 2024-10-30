from settings import *  # noqa

DEBUG = False

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

INSTALLED_APPS += [  # noqa
    "django_audit_log_middleware",
]

MIDDLEWARE += [  # noqa
    "django_audit_log_middleware.AuditLogMiddleware",
]

# Audit log middleware user field
AUDIT_LOG_USER_FIELD = "username"
