from .non_prod_base import *  # NOQA
import environ

INSTALLED_APPS += [  # noqa
    "behave_django",
]

env = environ.Env()

SECRET_KEY = env.str("ICMS_SECRET_KEY", default="test")

# speed up tests; see https://docs.djangoproject.com/en/3.0/topics/testing/overview/#password-hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Email
AWS_SES_ACCESS_KEY_ID = env.str("AWS_SES_ACCESS_KEY_ID", "test")
AWS_SES_SECRET_ACCESS_KEY = env.str("AWS_SES_SECRET_ACCESS_KEY", "test")
EMAIL_FROM = env.str("ICMS_EMAIL_FROM", "test@example.com")

CELERY_TASK_ALWAYS_EAGER = True

# SELENIUM
SELENIUM_BROWSER = "chrome"
SELENIUM_HUB_HOST = "selenium-hub"
SELENIUM_HOST = "web"
