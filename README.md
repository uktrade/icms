<!-- [![circle-ci-image]][circle-ci] -->
<!-- [![codecov-image]][codecov] -->

[![image](https://circleci.com/gh/uktrade/icms/tree/master.svg?style=svg)](https://circleci.com/gh/uktrade/icms/tree/master)
[![image](https://codecov.io/gh/uktrade/icms/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/icms)

# ICMS - Import Case Management System

## Introduction

ICMS is "Import Case Management System", and this repo contains the Python /
Django / PostgreSQL port of it from the original Oracle-based system.

## Requirements

- [Python 3.7+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/)
- Development only
  - [Docker Compose 1.21.0+](https://docs.docker.com/compose/)

## Setup

## Viewflow

ICMS uses the PRO version of [Viewflow](http://viewflow.io/) and in order to
fetch it from the private viewflow index `ICMS_VIEWFLOW_LICENSE` must be set.
Get it from [Rattic](https://rattic.ci.uktrade.digital/) ("Viewflow License
Key") and save it in `.env`:

    # use actual license number in place of <license_number>
    echo "ICMS_VIEWFLOW_LICENSE=<license_number>" > .env

`.env` file is ignored by git, make sure not to include this file in the
repository. It is only used locally.

## Local virtualenv

A local virtualenv is needed for a few reasons:

1. To be able to run the pre-commit checks
1. If using an IDE, so it has access to the library code and tooling

Note that the application is never actually run on the local machine while
developing, only within Docker.

## Initial setup

- `make build`
  - Build all Docker containers
- `make setup`
  - Create local virtualenv, set up pre-commit hooks, initialize database
- `make local_s3`
  - Create fake local S3 bucket. Local development uses
    [localstack](https://github.com/localstack/localstack) to emulate S3
    locally.

  - You will need aws cli tools installed and configured. If you have not done
    so run `aws configure`, the values don't really matter but aws cli won't run
    without a configuration file created.

  - The S3 bucket is named `icms.dev` on the localstack S3 instance. The
    localstack UI can be found on http://localhost:8081 and used to verify that
    the S3 bucket is created.

- `make createsuperuser`
  - Create user to login with

## Running the application

Start everything using docker-compose: `make debug`

Go to http://localhost:8080, login with the superuser account you created earlier.

Above script will start a PostgreSQL database and ICMS app in debug mode. In
order to run with no debug and Gunicorn server for a production-like environment
use: `make run`

Make sure to rebuild the Docker images if new dependencies are added to the
requirements files: `make build`.

## Code style

ICMS uses [Black](https://pypi.org/project/black/) for code formatting and
[flake8](https://flake8.pycqa.org/en/latest/) for code analysis. Useful commands:

- `make black` - Check code is formatted correctly
- `make black_format` - Reformat all code
- `make flake8` - Check code quality is up to scratch

## Deployments

- Dev deployment Jenkins job: https://jenkins.ci.uktrade.digital/job/icms/
- ci-pipeline config: https://github.com/uktrade/ci-pipeline-config/blob/master/icms.yaml


## Environment Variables

| Environment variable              | Default                                    | Notes                                                  |
| --------------------------------- | ------------------------------------------ | ---------------------------------                      |
| ICMS_DEBUG                        | False                                      |                                                        |
| ICMS_WEB_PORT                     | 8080                                       |                                                        |
| DATABASE_URL                      | postgres://postgres@db:5432/postgres       | Format postgres://username/password@host:port/database |
| ICMS_MIGRATE                      | True                                       | Runs Django migrate before starting the app            |
| ICMS_SECRET_KEY                   | random                                     | Django secret key                                      |
| ICMS_ALLOWED_HOSTS                | localhost                                  | Comma separated list of hosts                          |
| ICMS_AWS_S3_ACCESS_KEY_ID         |                                            | Access Key ID from AWS console                         |
| ICMS_AWS_S3_SECRET_ACCESS_KEY     |                                            | Secret Access Key from AWS console                     |
| ICMS_AWS_S3_REGION                |                                            | E.g. eu-west-2                                         |
| ICMS_AWS_S3_BUCKET_NAME           |                                            | E.g. ICMS                                              |
| ICMS_CLAMAV_URL                   |                                            | E.g. https://test:pass@clamav.digital/v2/scan          |
| ELASTIC_APM_SECRET_TOKEN          |                                            | Elastic APM server secret token for sending metrics    |
| ELASTIC_APM_ENVIRONMENT          |                                             | ICMS deployment env to separate metrics per env. e.g. prod|
| ELASTIC_APM_URL          |                                                     | Elastic APM server URL                                 |
