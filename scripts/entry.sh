#!/bin/sh -e
ICMS_WEB_PORT="${ICMS_WEB_PORT:-8080}"
ICMS_DEBUG="${ICMS_DEBUG:-False}"
APP_ENV="${APP_ENV:-dev}"
ALLOW_DATA_MIGRATION="${ALLOW_DATA_MIGRATION:-False}"

echo "ICMS running now with debug $ICMS_DEBUG"

echo "Running migrations"
python manage.py migrate

if [ "$ICMS_DEBUG" = 'False' ]; then
  python manage.py collectstatic --noinput --traceback
  python manage.py compress --engine jinja2
  gunicorn config.wsgi --config config/gunicorn.py
else
  python manage.py runserver 0:"$ICMS_WEB_PORT"
fi
