#!/bin/sh -e

echo "Running migrations"
python manage.py migrate

echo "Starting server"
opentelemetry-instrument gunicorn config.wsgi --config config/gunicorn.py
