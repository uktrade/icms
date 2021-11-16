# flake8: noqa: F405
from web.utils.sentry import init_sentry

from .non_prod_base import *

SECRET_KEY = env.str("ICMS_SECRET_KEY")
DATABASES = {"default": env.db("DATABASE_URL")}
ALLOWED_HOSTS = env.list("ICMS_ALLOWED_HOSTS")

init_sentry()
