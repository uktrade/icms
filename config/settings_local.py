# flake8: noqa: F405
from .settings import *

DEBUG = True

# for https://github.com/uktrade/django-chunk-s3-av-upload-handlers
AWS_REGION = "eu-west-2"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"
AWS_STORAGE_BUCKET_NAME = "icms.local"
AWS_S3_ENDPOINT_URL = env.local_aws_s3_endpoint_url

INSTALLED_APPS += [
    "django_extensions",
]

# When debugging queries in console
SHOW_DB_QUERIES = env.show_db_queries

if SHOW_DB_QUERIES:
    MIDDLEWARE += ["web.middleware.common.DBQueriesMiddleware"]

NPM_STATIC_FILES_LOCATION = "web/static/3rdparty"

NPM_FILE_PATTERNS = {
    "jquery": ["dist/jquery.min.js"],
    "jquery-ui-dist": ["jquery-ui.min.js"],
    "html5shiv": ["dist/html5shiv.min.js"],
    "jodit": ["build/jodit.min.*"],
    "jquery-fontspy": ["jQuery-FontSpy.js"],
    "select2": ["dist/css/select2.min.css", "dist/js/select2.min.js"],
    "sticky-kit": ["dist/sticky-kit.min.js"],
}

GRAPH_MODELS = {
    "all_applications": True,
    "group_models": True,
}

# minifi html (django-htmlmin)
HTML_MINIFY = False

# Django Compressor
COMPRESS_OFFLINE = not DEBUG

# django-ratelimit
RATELIMIT_ENABLE = False

# celery settings
# sometimes we want to run celery tasks synchronously to help with debugging
CELERY_TASK_ALWAYS_EAGER = env.celery_task_always_eager
CELERY_EAGER_PROPAGATES_EXCEPTIONS = env.celery_eager_propagates_exceptions
