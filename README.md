<!-- [![circle-ci-image]][circle-ci] -->
<!-- [![codecov-image]][codecov] -->

[![image](https://circleci.com/gh/uktrade/icms/tree/main.svg?style=svg)](https://circleci.com/gh/uktrade/icms/tree/main)
[![image](https://codecov.io/gh/uktrade/icms/branch/main/graph/badge.svg)](https://codecov.io/gh/uktrade/icms)

# ICMS - Import Case Management System

## Introduction

ICMS is "Import Case Management System", and this repo contains the Python /
Django / PostgreSQL port of it from the original Oracle-based system.

See [ICMS Features](documentation/icms-features.md) for an overview of the system.

## Requirements

- [Python 3.11.*](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/)
- Development only
  - [Docker Compose 1.21.0+](https://docs.docker.com/compose/)

## Setup

## Local virtualenv

A local virtualenv is needed for a few reasons:

1. To be able to run the pre-commit checks
1. If using an IDE, so it has access to the library code and tooling

Note that the application is never actually run on the local machine while
developing, only within Docker.

## Initial setup

- copy `.env.local-docker` to `.env`.
  - There are a few values you may need later stored in vault / ask another dev for correct values.
  - If you want to see all database queries done by each request, add `SHOW_DB_QUERIES=True` to it.
- `make build`
  - Build all Docker containers
- `make setup`
  - Create local virtualenv, set up pre-commit hooks, initialize database
- `make debug`
  - Run the application (needed to run make local_s3)
- `make local_s3`
  - Create fake local S3 bucket. Local development uses
    [localstack](https://github.com/localstack/localstack) to emulate S3
    locally.

  - You will need aws cli tools installed and configured. If you have not done
    so run `aws configure`, the values don't really matter but aws cli won't run
    without a configuration file created.

  - The S3 bucket is named `icms.local` on the localstack S3 instance. The
    localstack UI can be found on http://localhost:8081 and used to verify that
    the S3 bucket is created.

- `make manage args="create_icms_groups"`
  - Create icms groups before adding dummy data

- `make add_dummy_data`
  - Create test user(s), add needed permissions to user(s), create dummy importer and exporter, etc

- `make manage args="set_icms_sites http://caseworker:8080 http://export-a-certificate:8080 http://import-a-licence:8080"`
  - Creates the sites for working on ICMS locally

- Add the following lines to your `/etc/hosts` file:
```
127.0.0.1   caseworker
127.0.0.1   export-a-certificate
127.0.0.1   import-a-licence
```

## Running the application

Start everything using docker-compose: `make debug`

Go to http://caseworker:8080, login with the one of the test accounts:
  - ilb_admin
  - ilb_admin_2
  - nca_admin
  - ho_admin
  - san_admin
  - san_admin_2
  - con_user

Go to http://import-a-licence:8080, login with the one of the test accounts:
  - importer_user
  - importer_agent

Go to http://export-a-certificate:8080, login with the one of the test accounts:
  - exporter_user
  - exporter_agent

The password is the same for each user: `admin`

Make sure to rebuild the Docker images if new dependencies are added to the
requirements files: `make build`.

## Testing

To run the unit tests:

`./run-tests.sh`

To run tests for a single file in a non-distributed manner (faster):

`./run-tests.sh --dist=no web/tests/foo/bar.by`

To run tests with a fresh test database:

`./run-tests.sh --create-db`

To run the tests with full coverage run (mainly done as part of CI pipeline):

`make test`

## Code style

ICMS uses [Black](https://pypi.org/project/black/) for code formatting and
[flake8](https://flake8.pycqa.org/en/latest/) for code analysis. Useful commands:

- `make black` - Check code is formatted correctly
- `make black_format` - Reformat all code
- `make isort_format` - Orders imports
- `make flake8` - Check code quality is up to scratch
- `pre-commit run --all-files` - Check all pre-commit hooks

## pre-commit hooks
ICMS uses the following tool: [pre-commit](https://pre-commit.com/)

pre-commit config file: `.pre-commit-config.yaml`

Common commands (local venv must be activated):
- `pre-commit autoupdate` - Get the latest version of all hooks
- `pre-commit run` - Check files staged for commit (git add)
- `pre-commit run --all-files` - Runs all pre-commit hooks

## PII Secret Check Hooks tool
ICMS uses the following tool: [PII Secret Check Hooks](https://github.com/uktrade/pii-secret-check-hooks)

It runs as a pre-commit hook defined in the above section
- `pre-commit gc; pre-commit clean` - Run if the hooks pass but the git commit fails

PII tool files:
- `pii-custom-regex.txt` - Add custom regexes for finding secret or PII identification
- `pii-ner-exclude.txt` - False positives to exclude
- `pii-secret-exclude.txt` - Files to exclude from the pii checks

Refer to its documentation for further details

## Permissions in ICMS

ICMS uses a combination of standard django permissions as well as django guardian object permissions.

See [this document](documentation/icms-permissions.md) for an overview of the system.

## Rebuilding the database

A complete reset of the application database can be performed using:

```
make down
docker volume rm icms_pgdata
make migrate
make manage args="create_icms_groups"
make add_dummy_data
make manage args="set_icms_sites http://caseworker:8080 http://export-a-certificate:8080 http://import-a-licence:8080"
```

Alternatively you can run the script found here: `./scripts/reset-local-docker-db`

# Recreating the migration files:

The following commands can be run to regenerate `web/migrations/0001_initial.py`.

```
rm web/migrations/*.py
make migrations
git restore web/migrations/0002_data_add_sites.py
make black_format
make isort_format
```

Alternatively you can run the script found here: `./scripts/reset-icms-migrations`

## Database schema generation

A schema for the database can be generated using the following django-extensions command:

- `python manage.py graph_models --output=output.png`

## Updating package-lock.json
Run the following to update the sub-dependencies of pinned packages:
```bash
npm i --package-lock-only
npm audit fix
```


## Updating Javascript dependencies (When they get updated):
Run the following command, this will install dependencies and copy them to the correct place

```bash
make requirements-web
```

see the following code for the config:

```
# icms/config/settings_local.py
NPM_STATIC_FILES_LOCATION =
NPM_FILE_PATTERNS
```

Currently, we only have this config defined in the settings_local.py config file.

## Deployments

- ICMS Jenkins view: https://jenkins.ci.uktrade.digital/view/ICMS/
- ci-pipeline config: https://github.com/uktrade/ci-pipeline-config/blob/master/icms.yaml

## File Uploads

Files are uploaded directly to S3 without being saved into file system of the
app. The app in turn sends the file to ClamAV for malware/virus checking. See
ICMSFileField.


## Environment Variables

See `.env.local-docker`

See also `docker-compose.yml` for additional debug environment variables.
