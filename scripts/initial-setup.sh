#!/bin/bash

set -e

echo "Installing swig (required by endesive)"
if [[ "$OSTYPE" == "darwin"* ]]; then
  which -s brew
  if [[ $? != 0 ]] ; then
      echo "Homebrew not installed, please install it first. This is required to install swig."
      exit 1
  fi
    brew install swig
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  sudo apt-get install swig
fi


echo "Creating virtualenv"
virtualenv --python=python3.11 .venv
. .venv/bin/activate

echo "Installing local requirements in a virtualenv"
pip install -U pip
pip install -r requirements-dev.txt

echo "Installing playwright chromium browser & dependencies"
pip install pytest-playwright
playwright install --with-deps chromium

echo "Installing pre-commit hooks"
pre-commit install

echo "Updating pre-commit hooks to latest"
pre-commit autoupdate

deactivate
