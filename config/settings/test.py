# flake8: noqa: F405
from .non_prod_base import *

SECRET_KEY = env.str("ICMS_SECRET_KEY", default="test")
DATABASES = {
    "default": env.db("DATABASE_URL", "postgres://postgres:password@db:5432/postgres")  # /PS-IGNORE
}
ALLOWED_HOSTS = ["localhost", "web"]
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
        # We don't want this noise when testing
        "django_structlog": {
            "propagate": False,
        },
    },
}
