# flake8: noqa: F405
from .settings import *

DEBUG = True

# speed up tests; see https://docs.djangoproject.com/en/3.0/topics/testing/overview/#password-hashing
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CELERY_TASK_ALWAYS_EAGER = True

# SELENIUM
SELENIUM_BROWSER = "chrome"
SELENIUM_HUB_HOST = "selenium-hub"
SELENIUM_HOST = "web"

# django-ratelimit
RATELIMIT_ENABLE = False

FILE_UPLOAD_HANDLERS = ("web.tests.file_upload_handler.DummyFileUploadHandler",)  # type: ignore[assignment]
APP_ENV = "test"

# Add so we can test the bypass chief views.
ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD = True

# Never send licences to chief when running tests.
SEND_LICENCE_TO_CHIEF = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "faker": {"level": "INFO"},
        "mohawk": {"level": "INFO"},
        "django_structlog": {"propagate": False},
        # https://github.com/Kozea/WeasyPrint/issues/412#issuecomment-1724928357
        "fontTools.subset": {"propagate": False},
    },
}

ICMS_V1_REPLICA_USER = ""
ICMS_V1_REPLICA_PASSWORD = ""
ICMS_V1_REPLICA_DSN = ""

GOV_NOTIFY_API_KEY = "fakekey-11111111-1111-1111-1111-111111111111-22222222-2222-2222-222222222222"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


#
# Staff-sso
STAFF_SSO_ENABLED = False
GOV_UK_ONE_LOGIN_ENABLED = False
LOGIN_URL = "accounts:login"
LOGOUT_REDIRECT_URL = "accounts:login"  # type: ignore[assignment]
