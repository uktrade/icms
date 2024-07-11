FROM python:3.11.4

# Install dependencies
RUN apt-get update && apt-get install  \
    # endesive dependency
    swig  \
    # psycopg[c] dependencies https://www.psycopg.org/psycopg3/docs/basic/install.html#local-installation
    python3-dev libpq-dev \
    # To compile static assets
    npm  \
    # poppler for PDF visual regression tests \
    poppler-utils \
    -y

ENV ICMS_WEB_PORT ${ICMS_WEB_PORT}

WORKDIR /code

COPY requirements-*.txt /code/

RUN pip install --no-cache-dir --upgrade -r requirements-dev.txt

# Install playwright dependencies & browsers (we only use chromium when building PDFs)
RUN playwright install --with-deps chromium

CMD local_deployment/entry.sh
