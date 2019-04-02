# Import Case Management System - Python/Django port on PostgreSQL database


<!-- [![circle-ci-image]][circle-ci] -->
<!-- [![codecov-image]][codecov] -->

---

## Requirements

[Python 3.7](https://www.python.org/downloads/release/python-372/)

[PostgreSQL](https://www.postgresql.org/)

## Development installation

    git clone https://github.com/uktrade/icms.git
    cd icms
    docker-compose up

Go to url http://localhost:8000

Above script will start a PostgreSQL database and ICMS app in debug mode with live reload functionality.

Make sure to rebuild the image  if new dependencies are installed and added to requirements.txt

    docker-compose up --build web
    

## Environment Variables

| Environment variable              | Default                                    | Notes                                                  |
| --------------------------------- | ------------------------------------------ | ---------------------------------                      |
| ICMS_DEBUG                        | False                                      |                                                        |
| ICMS_WEB_PORT                     | 8000                                       |                                                        |
| ICMS_DB_URL                       | postgres://postgres@db:5432/postgres       | Format postgres://username/password@host:port/database |
| ICMS_MIGRATE                      | True                                       | Runs Django migrate before starting the app            |
| ICMS_SECRET_KEY                   | random                                     | Django secret key                                      |
| ICMS_ALLOWED_HOSTS                |                                            | Comma separated list of hosts                          |

