#!/bin/bash

set -e

export DJANGO_SETTINGS_MODULE=config.settings_test

# some tests require static files to be collected, e.g. the pdf file generation tests
docker compose run --rm web python manage.py collectstatic --noinput
# we are using this work flow:
# https://pytest-django.readthedocs.io/en/latest/database.html#example-work-flow-with-reuse-db-and-create-db
#
# we have --reuse-db in pytest.ini, so repeated test runs by developers locally
# are fast. if you change the database schema, you have to do ""./run-test.sh
# --create-db" to force re-creation of the test database
#
# For speed run with --dist=no when testing a single file
docker compose run --rm web pytest --ignore web/end_to_end --tb=short -n=auto --dist=loadfile "$@"

# With coverage (terminal report)
#docker compose run --rm web \
#  pytest --ignore web/end_to_end --tb=short \
#  --cov=web \
#  --cov=config \
#  --cov-report term-missing \
#  --dist=loadfile \
#  -n=auto "$@"
