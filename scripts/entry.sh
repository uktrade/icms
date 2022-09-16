#!/bin/sh -e
ICMS_WEB_PORT="${ICMS_WEB_PORT:-8080}"
ICMS_DEBUG="${ICMS_DEBUG:-False}"
APP_ENV="${APP_ENV:-dev}"
ALLOW_DATA_MIGRATION="${ALLOW_DATA_MIGRATION:-False}"

if [ "$ALLOW_DATA_MIGRATION" = 'True' ] && [ "$APP_ENV" = 'production' ]; then
  echo "Creating oracle directory"
  mkdir -p oracle
  echo "Downloading zipped oracle instant client"
  curl -L https://download.oracle.com/otn_software/linux/instantclient/215000/instantclient-basiclite-linux.x64-21.5.0.0.0dbru.zip \
    -o oracle/instantclient-basiclite-linux.x64-21.5.0.0.0dbru.zip
  echo "Unzipping oracle instant client"
  unzip oracle/instantclient-basiclite-linux.x64-21.5.0.0.0dbru.zip -d oracle
  echo "Removing zipped oracle instant client"
  rm oracle/instantclient-basiclite-linux.x64-21.5.0.0.0dbru.zip
fi

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
