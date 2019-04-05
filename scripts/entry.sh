#!/bin/sh -e

ICMS_WEB_PORT="${ICMS_WEB_PORT:-8080}"

echo "ICMS running now with debug $ICMS_DEBUG"

if [ "${ICMS_MIGRATE:-True}" = 'True' ]; then
  echo "Running migrations"
  python manage.py migrate
fi

if [ "${ICMS_DEBUG:-False}" = 'True' ]; then
  python manage.py runserver 0:"$ICMS_WEB_PORT"
else
  gunicorn icms.wsgi \
           --name icms \
           --workers "${ICMS_NUM_WORKERS:-3}" \
           --bind 0:"$ICMS_WEB_PORT"
fi
