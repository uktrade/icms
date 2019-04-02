import environ
from django.core.management.utils import get_random_secret_key

env = environ.Env(
    # set casting, default value
    ICMS_DEBUG=(bool, False),
    ICMS_WEB_PORT=(int, 8000),
    # #No ICMS prefix for db as GOV PaaS sets DATABASE_URL variable automatically
    DATABASE_URL=(str, 'postgres://postgres@db:5432/postgres'),
    ICMS_SECRET_KEY=(str, get_random_secret_key()),
    ICMS_ALLOWED_HOSTS=(list, []))
