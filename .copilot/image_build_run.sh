#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

# Add commands below to run inside the container after all the other buildpacks have been applied
export BUILD_STEP='True'
export COPILOT_ENVIRONMENT_NAME='build'

python manage.py collectstatic --noinput --traceback

# TODO: Fix CommandError: An error occurred during rendering /workspace/web/templates/base.html: Missing connections string
# python manage.py compress --force --engine jinja2

# TODO: Needs sorting for PDF generation
#PLAYWRIGHT_BROWSERS_PATH="/workspace/playwright-deps" python -m playwright install --with-deps chromium
