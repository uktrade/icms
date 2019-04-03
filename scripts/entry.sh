#!/bin/sh -e
live_reload_pid=

if [ "${ICMS_MIGRATE:-True}" = 'True' ]; then
  echo "Running migrations"
  python manage.py migrate
fi

python manage.py runserver 0:"${ICMS_WEB_PORT:-8080}"
