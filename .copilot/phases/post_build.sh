#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

# Add commands below to run as part of the post_build phase

echo "Running post build..."

if [ "$APP_ENV" == "dev" ]
then
  echo "Running end to end tests"
  make end_to_end_test_remote_dev
fi
