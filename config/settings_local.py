# flake8: noqa: F405
from .settings import *

DEBUG = True

# for https://github.com/uktrade/django-chunk-s3-av-upload-handlers
AWS_REGION = "eu-west-2"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"
AWS_STORAGE_BUCKET_NAME = "icms.local"
AWS_S3_ENDPOINT_URL = env.local_aws_s3_endpoint_url

# Debug toolbar config
INTERNAL_IPS = ("127.0.0.1", "localhost")
INSTALLED_APPS += [
    "debug_toolbar",
    "django_extensions",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# When debugging queries in console
SHOW_DB_QUERIES = env.show_db_queries

if SHOW_DB_QUERIES:
    MIDDLEWARE += ["web.middleware.common.DBQueriesMiddleware"]

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
]

SHOW_DEBUG_TOOLBAR = env.show_debug_toolbar

DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
    "SHOW_TOOLBAR_CALLBACK": lambda x: SHOW_DEBUG_TOOLBAR,
}

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

# Django Compressor (also set ICMS_DEBUG to False, to trigger compression of js on system start)
COMPRESS_OFFLINE = False

# Override asim handler locally (easier to read console handler)
LOGGING["loggers"]["django"]["handlers"] = ["console"]

# django-ratelimit
RATELIMIT_ENABLE = False

# celery settings
# sometimes we want to run celery tasks synchronously to help with debugging
CELERY_TASK_ALWAYS_EAGER = env.celery_task_always_eager
CELERY_EAGER_PROPAGATES_EXCEPTIONS = env.celery_eager_propagates_exceptions
