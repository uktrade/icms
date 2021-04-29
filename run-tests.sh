#!/bin/bash

set -e

export DJANGO_SETTINGS_MODULE=config.settings.test
export ICMS_DEBUG=False

# we are using this work flow:
# https://pytest-django.readthedocs.io/en/latest/database.html#example-work-flow-with-reuse-db-and-create-db
#
# we have --reuse-db in pytest.ini, so repeated test runs by developers locally
# are fast. if you change the database schema, you have to do ""./run-test.sh
# --create-db" to force re-creation of the test database.

docker-compose run --rm web pytest --tb=short --dist=loadfile --tx=4*popen "$@"
