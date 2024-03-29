#!/bin/sh -e

echo "Running migrations"
python manage.py migrate

if [ -n "${COPILOT_ENVIRONMENT_NAME}" ]; then
    echo "Running in DBT Platform"
    opentelemetry-instrument gunicorn config.wsgi --config config/gunicorn.py
else
    echo "Running in Cloud Foundry"

    # In DBT platform the following will be done at the build stage
    echo "Installing playwright chromium browser"
    playwright install chromium

    echo "Collecting static files"
    python manage.py collectstatic --noinput --traceback
    python manage.py compress --engine jinja2

    gunicorn config.wsgi --config config/gunicorn.py
fi
