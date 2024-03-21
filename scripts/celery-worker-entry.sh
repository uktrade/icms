#!/bin/sh -e

if [ -n "${COPILOT_ENVIRONMENT_NAME}" ]; then
    echo "Running in DBT Platform"
    celery --app=config.celery:app worker --loglevel=INFO -Q celery,mail,reports
else
    echo "Running in Cloud Foundry"
    # In DBT platform the following will be done at the build stage
    echo "Installing playwright chromium browser for celery worker."
    playwright install chromium

    celery --app=config.celery:app worker --loglevel=INFO -Q celery,mail,reports
fi
