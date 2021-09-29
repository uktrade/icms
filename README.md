<!-- [![circle-ci-image]][circle-ci] -->
<!-- [![codecov-image]][codecov] -->

[![image](https://circleci.com/gh/uktrade/icms/tree/master.svg?style=svg)](https://circleci.com/gh/uktrade/icms/tree/master)
[![image](https://codecov.io/gh/uktrade/icms/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/icms)

# ICMS - Import Case Management System

## Introduction

ICMS is "Import Case Management System", and this repo contains the Python /
Django / PostgreSQL port of it from the original Oracle-based system.

## Requirements

- [Python 3.9+](https://www.python.org/downloads/)
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

  - The S3 bucket is named `icms.local` on the localstack S3 instance. The
    localstack UI can be found on http://localhost:8081 and used to verify that
    the S3 bucket is created.

- `make add_dummy_data`
  - Create test user(s), add needed permissions to user(s), create dummy importer and exporter, etc

- Ask somebody for a copy of `.env`.
  - If you want to see all database queries done by each request, add `SHOW_DB_QUERIES=True` to it.

## Running the application

Start everything using docker-compose: `make debug`

Go to http://localhost:8080, login with the superuser account you created earlier.

Above script will start a PostgreSQL database and ICMS app in debug mode.

Make sure to rebuild the Docker images if new dependencies are added to the
requirements files: `make build`.

## Testing

To run the unit tests:

`./run-tests.sh`

To run tests for a single file in a non-distributed manner (faster):

`./run-tests.sh --dist=no web/tests/foo/bar.by`

To run tests with a fresh test database:

`./run-tests.sh --create-db`

## Code style

ICMS uses [Black](https://pypi.org/project/black/) for code formatting and
[flake8](https://flake8.pycqa.org/en/latest/) for code analysis. Useful commands:

- `make black` - Check code is formatted correctly
- `make black_format` - Reformat all code
- `make flake8` - Check code quality is up to scratch

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

see the following file for the config:

```
# icms/config/settings/development.py
NPM_STATIC_FILES_LOCATION =
NPM_FILE_PATTERNS
```

Currently we only have this config defined in the development.py settings file.


## Rebuilding the database

A complete reset of the application database can be performed using:

```
make down
docker volume rm icms_pgdata
make migrate
make add_dummy_data
```

# Recreating the migration files:

The following commands can be run to regenerate `web/migrations/0001_initial.py` and then checkout the data migrations.

```
rm web/migrations/*.py
make migrations
git checkout -- web/migrations/*_data.py
make black_format
make isort_format
```

## Deployments

- Dev deployment Jenkins job: https://jenkins.ci.uktrade.digital/job/icms/
- ci-pipeline config: https://github.com/uktrade/ci-pipeline-config/blob/master/icms.yaml

## Business Processes

## File Uploads

Files are uploaded directly to S3 without being saved into file system of the
app. The app in turn sends the file to ClamAV for malware/virus checking. See
ICMSFileField.

### Further Information Request Process

Further Information Request process (FIR) are sent by case officers to importers/exporters as part of various access requests, import/export applications.

A Further Information Request can not exist on it's own. It needs a parent process to be attached to.

In order to add FIR processes to a parent process follow the steps below. Examples are from `ImporterAccessRequestProcess`

-   Add `FurtherInformationProcessMixin` to your process model with a generic relation for FIR processes named `fir_processes`

```python
from web.domains.case.fir.mixins import FurtherInformationProcessMixin
from web.domains.case.fir.models import FurtherInformationRequestProcess

class ImporterAccessRequestProcess(FurtherInformationProcessMixin, Process):
	fir_processes = GenericRelation(FurtherInformationRequestProcess)
```

- Implement mixin's method interface to obtain necessary runtime data for the flow ( permissions, team, namespace etc.)

```python

def fir_config(self):
    """Returns configuration required for FIR processes to run.

        Example Config:

          {
            'requester_permission': 'web.IMP_CASE_OFFICER',
            'responder_permission': 'web.IMP_EDIT_APP',
            'responder_team': 'web.IMP_EDIT_APP',
            'namespace': 'access:importer'
          }"""
        raise NotImplementedError

    def fir_content(self, request):
        """Returns initial FIR content for requester to edit.

            Example:

            {
                'request_subject': 'subject',
                'request_detail': 'detail',
            }"""
        raise NotImplementedError

    def on_fir_create(self, fir):
        """Invoked when a new FIR process is started.
            Returns a FurtherInformationRequest instance

            Parameter: fir - New Furhter Information Request"""
        raise NotImplementedError
```

- Add FIR start and list urls to your process urls

```python

  from web.domains.case.fir.urls import fir_parent_urls

  importer_access_request_urls = FlowViewSet(ImporterAccessRequestFlow).urls
  importer_access_request_urls.extend(fir_parent_urls)

```

FIR views will be accessible with url name `<parent_process_namespace>:fir-list` and `<parent_process_namespace:fir-new>`.

In case of importer access requests it is `access:importer:fir-list` and `access:importer:fir-new`


## Environment Variables

| Environment variable              | Default                                    | Notes                                                  |
| --------------------------------- | ------------------------------------------ | ---------------------------------                      |
| ICMS_DEBUG                        | False                                      |                                                        |
| ICMS_WEB_PORT                     | 8080                                       |                                                        |
| DATABASE_URL                      | postgres://postgres@db:5432/postgres       | Format postgres://username/password@host:port/database |
| ICMS_MIGRATE                      | True                                       | Runs Django migrate before starting the app            |
| ICMS_SECRET_KEY                   | random                                     | Django secret key                                      |
| ICMS_ALLOWED_HOSTS                | localhost                                  | Comma separated list of hosts                          |
| AWS_REGION                        |                                            | E.g. eu-west-2                                         |
| AWS_ACCESS_KEY_ID                 |                                            | Access Key ID from AWS console                         |
| AWS_SECRET_ACCESS_KEY             |                                            | Secret Access Key from AWS console                     |
| AWS_STORAGE_BUCKET_NAME           |                                            | E.g. icms.staging                                      |
| CLAM_AV_DOMAIN                    |                                            | E.g. scan.com                                          |
| CLAM_AV_USERNAME                  |                                            |                                                        |
| CLAM_AV_PASSWORD                  |                                            |                                                        |
| ELASTIC_APM_SECRET_TOKEN          |                                            | Elastic APM server secret token for sending metrics    |
| ELASTIC_APM_ENVIRONMENT           |                                            | deployment env to separate metrics per env. e.g. prod  |
| ELASTIC_APM_URL                   |                                            | Elastic APM server URL                                 |
