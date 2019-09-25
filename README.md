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

    git clone https://github.com/uktrade/icms.git
    cd icms
    make debug

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
| ICMS_ALLOWED_HOSTS                | localhost                                  | Comma separated list of hosts                                       |
| ICMS_AWS_ACCESS_KEY_ID            |                                            | Access Key ID from AWS console                                       |
| ICMS_AWS_SECRET_ACCESS_KEY        |                                            | Secret Access Key from AWS console                                       |
| ICMS_AWS_REGION                   |                                            | E.g. eu-west-2                                      |
| ICMS_AWS_S3_BUCKET_NAME           |                                            | E.g. ICMS                          |

