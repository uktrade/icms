FROM python:3.11.4

# Install dependencies
RUN apt-get update && apt-get install wget graphviz libgraphviz-dev gcc libpq-dev postgresql-client npm -y

ENV ICMS_WEB_PORT ${ICMS_WEB_PORT}

WORKDIR /code

COPY requirements-*.txt /code/

RUN pip install --no-cache-dir --upgrade -r requirements-dev.txt

CMD scripts/entry.sh
