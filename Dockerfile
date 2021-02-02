FROM python:3.7.6-slim

# Install dependencies
RUN apt-get update && apt-get install wget graphviz libgraphviz-dev gcc postgresql-client npm -y

ENV DOCKERIZE_VERSION v0.6.1
ENV PYTHONBUFFERED 1
ENV ICMS_WEB_PORT ${ICMS_WEB_PORT}

RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN pip3 install --upgrade pip

RUN mkdir /code
RUN mkdir /deps

WORKDIR /code

COPY requirements-*.txt /code/

RUN pip3 install -r requirements-dev.txt

CMD scripts/entry.sh
