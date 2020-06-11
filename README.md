# Import Case Management System - Python/Django port on PostgreSQL database

[![image](https://circleci.com/gh/uktrade/icms/tree/master.svg?style=svg)](https://circleci.com/gh/uktrade/icms/tree/master)
[![image](https://codecov.io/gh/uktrade/icms/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/icms)

<!-- [![circle-ci-image]][circle-ci] -->
<!-- [![codecov-image]][codecov] -->

---

## Requirements

[Python 3.7+](https://www.python.org/downloads/release/python-372/)


[PostgreSQL](https://www.postgresql.org/)

## Development requirements

[Docker Compose 1.23.2+](https://docs.docker.com/compose/)



## Development installation

  ICMS uses PRO version of [Viewflow](http://viewflow.io/), in order to fetch PRO package from private viewflow index `ICMS_VIEWFLOW_LICENSE` must be set.

  Ask your teammates or Webops team for license number.

  `.env` file is ignored by git, make sure not to include this file in the repository and it is only used locally

    git clone https://github.com/uktrade/icms.git
    cd icms
    echo "ICMS_VIEWFLOW_LICENSE=<license_number>" > .env   #  use actual license number in place of <license_number>
    make setup # only needed on first run or after freshly build containers
    make debug
    make local_S3 # only needed on first run or after freshly build containers
    make createsuperuer # to create a superuser

### Local AWS S3
    Local development used [localstack](https://github.com/localstack/localstack) to emulate S3 locally

    You will need aws cli tools installed and configured, if you have not done so run`aws configure` the values don't really matter but aws cli won't run without a configuration file created.

    `make local_S3` will create an S3 bucket named `icms.dev` on the localstack S3 instance

    localstack UI can be found on http://localhost:8081 and used to very the if S3 bucket is created

Go to url http://localhost:8080

Above script will start a PostgreSQL database and ICMS app in debug mode. In order to run with no debug and Gunicorn server for a production-like environment use:

    make run

Make sure to rebuild the image if new dependencies are installed and added to requirements.txt

    make build

or build and run using:

    make build debug

or

    make build run


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

