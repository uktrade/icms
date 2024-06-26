"""
WSGI config for icms project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from dbt_copilot_python.utility import is_copilot
from django.core.wsgi import get_wsgi_application
from opentelemetry.instrumentation.wsgi import OpenTelemetryMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()


# is_copilot() evaluates to True locally now so also check APP_ENV
# This was done to use DBTPlatformEnvironment instead of CloudFoundryEnvironment going forward.
if is_copilot() and os.environ.get("APP_ENV", "") != "local":
    application = OpenTelemetryMiddleware(application)
