#!/bin/sh -e

echo "Check missing migrations"
python manage.py makemigrations --check --dry-run

echo "Starting server on port: ${ICMS_WEB_PORT}"
python manage.py runserver 0.0.0.0:$ICMS_WEB_PORT
