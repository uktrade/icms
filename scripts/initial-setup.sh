#!/bin/bash

set -e

export ICMS_VIEWFLOW_LICENSE=$(cat .env | grep ICMS_VIEWFLOW_LICENSE | cut -d= -f2)

virtualenv --python=python3 .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
deactivate

git-hooks/setup.sh
