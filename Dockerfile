FROM python:3-alpine
ENV PYTHONBUFFERED 1
ENV ICMS_WEB_PORT ${ICMS_WEB_PORT}
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN \
  apk add --no-cache postgresql-libs postgresql-client && \
  apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
  python3 -m pip install -r requirements.txt --no-cache-dir && \
  apk --purge del .build-deps
COPY . /code/
CMD scripts/entry.sh
