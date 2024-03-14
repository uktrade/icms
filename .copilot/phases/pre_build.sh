#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

# Add commands below to run as part of the pre_build phase

# Must have a central requirements.txt
echo "-r requirements-prod.txt" > requirements.txt
