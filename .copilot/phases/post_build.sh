#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

# Add commands below to run as part of the post_build phase

echo "Running post build..."

if [ "$APP_ENV" == "dev" ]
then
  echo "Starting post build phase"
  pip install -r requirements-playwright.txt
  pytest -c playwright/pytest.ini web/end_to_end/
fi
