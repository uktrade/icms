#!/bin/sh -e

ICMS_WEB_PORT="${ICMS_WEB_PORT:-8080}"
ICMS_DEBUG="${ICMS_DEBUG:-False}"
ICMS_NUM_WORKERS="${ICMS_NUM_WORKERS:-3}"
DATABASE_URL="${DATABASE_URL:-postgres://postgres@db:5432/postgres}"

retry=10

wait_for_db() {
  if [ ${retry} -eq 0 ]; then
    echo "Database access timedout" 1>&2
    exit 1;
  fi

  if pg_isready -d "${DATABASE_URL}"; then
    echo "OK";
  else
    retry=$((retry-1))
    sleep 1;
    echo "Retrying database access"
    wait_for_db
  fi
}

echo "Waiting for db access"
wait_for_db

echo "ICMS running now with debug $ICMS_DEBUG"

if [ "${ICMS_MIGRATE:-True}" = 'True' ]; then
  echo "Running migrations"
  python manage.py migrate
fi

if [ "$ICMS_DEBUG" = 'True' ]; then
  python manage.py runserver 0:"$ICMS_WEB_PORT"
else
  gunicorn config.wsgi \
           --name icms \
           --workers "$ICMS_NUM_WORKERS" \
           --bind 0:"$ICMS_WEB_PORT"
fi
