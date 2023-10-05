FROM python:3.11.4

# Install dependencies
RUN apt-get update && apt-get install wget graphviz libgraphviz-dev gcc libpq-dev postgresql-client npm -y

ENV ICMS_WEB_PORT ${ICMS_WEB_PORT}

RUN pip3 install --upgrade pip

RUN mkdir /code
RUN mkdir /deps

WORKDIR /code

COPY requirements-*.txt /code/

RUN pip3 install -r requirements-dev.txt

CMD scripts/entry.sh
