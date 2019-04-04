#!/bin/sh -e

stop_live_reload() {
  echo "Stopping live reload"
  [ -z "$live_reload_pid" ] || \
    kill "$live_reload_pid"
}

if [ "${ICMS_MIGRATE:-True}" = 'True' ]; then
  echo "Running migrations"
  python manage.py migrate
fi

if [ "${ICMS_DEBUG:-False}" = 'True' ]; then
  echo "Starting live reload"
  python manage.py livereload &
  live_reload_pid=$!
  trap "stop_live_reload" EXIT
fi

python manage.py runserver 0:"${ICMS_WEB_PORT:-8000}"
