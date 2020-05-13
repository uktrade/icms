FROM python:3.7.6-alpine
ENV PYTHONBUFFERED 1
ENV ICMS_WEB_PORT ${ICMS_WEB_PORT}
ENV DOCKERIZE_VERSION v0.6.1
ARG ICMS_VIEWFLOW_LICENSE
RUN mkdir /code
RUN mkdir /deps
WORKDIR /code
COPY Pipfile Pipfile.lock /code/

RUN [ ! -z "${ICMS_VIEWFLOW_LICENSE}" ] || { echo "Viewflow license key cannot be empty"; exit 1; }

# Install dependencies
RUN \
  apk add --no-cache postgresql-libs openssl gcc musl-dev postgresql-dev npm postgresql-client && \
  python3 -m pip install --upgrade pip && \
  python3 -m pip install pipenv && \
  python3 -m pipenv install --system --dev --deploy

# Install dockerize
RUN \
  wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
  && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
  && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz

COPY . /code/
CMD scripts/entry.sh
