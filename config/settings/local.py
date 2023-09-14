# flake8: noqa: F405
from .non_prod_base import *

SECRET_KEY = env.str("ICMS_SECRET_KEY", default="development")
DATABASES = {
    "default": env.db("DATABASE_URL", "postgres://postgres:password@db:5432/postgres")  # /PS-IGNORE
}
ALLOWED_HOSTS = [
    "localhost",
    "web",
    "caseworker",
    "import-a-licence",
    "export-a-certificate",
]
DEBUG = True

# for https://github.com/uktrade/django-chunk-s3-av-upload-handlers
AWS_REGION = "eu-west-2"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"
AWS_STORAGE_BUCKET_NAME = "icms.local"
AWS_S3_ENDPOINT_URL = "http://localstack:4566/"

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
SHOW_DB_QUERIES = env.bool("SHOW_DB_QUERIES", False)

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

DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
    "SHOW_TOOLBAR_CALLBACK": lambda x: False if "DISABLE_DEBUG_TOOLBAR" in os.environ else True,
}

NPM_STATIC_FILES_LOCATION = "web/static/3rdparty"

NPM_FILE_PATTERNS = {
    "jquery": ["dist/jquery.min.js"],
    "jquery-ui-dist": ["jquery-ui.min.js"],
    "html5shiv": ["dist/html5shiv.min.js"],
    "jquery.formset": ["src/jquery.formset.js"],
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


# Need to use the local docker-compose network name to access the static files.
PDF_DEFAULT_DOMAIN = "http://web:8080/"

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
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "level": "INFO",
        },
        "web": {"level": "DEBUG"},
        # We don't want this noise locally
        "django_structlog": {
            "propagate": False,
        },
        # Uncomment if needed (Used when debugging mohawk stuff)
        # "mohawk": {
        #     'handlers': ['console'], "level": "DEBUG"
        # },
        # "urllib3": {
        #     'handlers': ['console'], "level": "DEBUG"
        # },
    },
}

# django-ratelimit
RATELIMIT_ENABLE = False
