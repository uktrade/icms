FROM python:3.7.6-alpine
ENV PYTHONBUFFERED 1
ENV ICMS_WEB_PORT ${ICMS_WEB_PORT}
ENV DOCKERIZE_VERSION v0.6.1
ARG ICMS_VIEWFLOW_LICENSE
RUN mkdir /code
RUN mkdir /deps
WORKDIR /code
COPY requirements-*.txt /code/

RUN [ ! -z "${ICMS_VIEWFLOW_LICENSE}" ] || { echo "Viewflow license key cannot be empty"; exit 1; }

# Install dependencies
RUN \
  apk add --no-cache postgresql-libs openssl build-base musl-dev postgresql-dev npm postgresql-client libffi-dev && \
  pip3 install --upgrade pip && \
  pip3 install -r requirements-dev.txt

# Install dockerize
RUN \
  wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
  && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
  && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz

CMD scripts/entry.sh
