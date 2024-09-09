#!/bin/bash

set -e

pip-compile --output-file=requirements-dev.txt requirements/requirements-dev.in
pip-compile --output-file=requirements-playwright.txt requirements/requirements-playwright.in
pip-compile --output-file=requirements-prod.txt requirements/requirements-prod.in
