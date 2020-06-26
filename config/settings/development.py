import environ
import os

from .non_prod_base import *  # NOQA”

env = environ.Env()

# Debug toolbar config
INTERNAL_IPS = ('127.0.0.1', 'localhost')
INSTALLED_APPS += [  # NOQA
    'debug_toolbar',
]

MIDDLEWARE += [  # NOQA
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': lambda x: False if 'DISABLE_DEBUG_TOOLBAR' in os.environ else True
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('ICMS_SECRET_KEY', default='development')
DEBUG = env.bool('ICMS_DEBUG', True)

# Email
AWS_SES_ACCESS_KEY_ID = env.str('AWS_SES_ACCESS_KEY_ID', 'dev')
AWS_SES_SECRET_ACCESS_KEY = env.str('AWS_SES_SECRET_ACCESS_KEY', 'dev')
EMAIL_FROM = env.str('ICMS_EMAIL_FROM',
                     'enquiries.ilb@icms.trade.dev.uktrade.io')

# Loging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':
            '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} - {message} [{module}]',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'web': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    },
}

NPM_STATIC_FILES_LOCATION = os.path.join('web', 'static', '3rdparty')

NPM_FILE_PATTERNS = {
    'jquery': [os.path.join('dist', 'jquery.min.js')],
    'jquery-ui-dist': ['jquery-ui.min.js'],
    'html5shiv': [os.path.join('dist', 'html5shiv.min.js')],
    'jquery.formset': [os.path.join('src', 'jquery.formset.js')],
    'jodit': [os.path.join('build', 'jodit.min.*')],
    'jquery-fontspy': ['jQuery-FontSpy.js'],
    'sticky-kit': [os.path.join('dist', 'sticky-kit.min.js')],
}

# Django Compressor - uncomment to activate (also set ICMS_DEBUG to False, to trigger compression of js on system start)
# COMPRESS_OFFLINE = True

# minifi html (djano-htmlmin) - uncomment to activate
# HTML_MINIFY = True
