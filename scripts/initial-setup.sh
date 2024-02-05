#!/bin/bash

set -e

virtualenv --python=python3.11 .venv
. .venv/bin/activate

echo "Installing local requirements in a virtualenv"
pip install -U pip
pip install -r requirements-dev.txt

echo "Installing pre-commit hooks"
pre-commit install

echo "Updating pre-commit hooks to latest"
pre-commit autoupdate

deactivate
