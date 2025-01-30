#!/bin/bash

echo "Running migrations"
python manage.py migrate

if [[ "$COPILOT_ENVIRONMENT_NAME" == "hotfix" ]]
then
  # we're on hotfix, let's reset the sites to the known hotfix URLs.
  echo "Setting hotfix sites"
  python manage.py set_icms_sites
fi

echo "Starting server"
opentelemetry-instrument gunicorn config.wsgi --config config/gunicorn.py
