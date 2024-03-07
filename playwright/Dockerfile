FROM mcr.microsoft.com/playwright/python:latest
# Available playwright tags:
# https://mcr.microsoft.com/en-us/product/playwright/tags

WORKDIR /code
COPY requirements-playwright.txt /code/

RUN pip install -r requirements-playwright.txt
