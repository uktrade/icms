#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

# Add commands below to run inside the container after all the other buildpacks have been applied
export BUILD_STEP='True'
export COPILOT_ENVIRONMENT_NAME='build'

echo "Running python manage.py collectstatic --noinput --traceback"
python manage.py collectstatic --noinput --traceback

echo "Running compress python manage.py compress --force --engine jinja2"
python manage.py compress --force --engine jinja2

echo "Running PLAYWRIGHT_BROWSERS_PATH="/workspace/playwright-deps" python -m playwright install"
PLAYWRIGHT_BROWSERS_PATH="/workspace/playwright-deps" python -m playwright install
