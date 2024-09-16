FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
# Available playwright tags:
# https://mcr.microsoft.com/en-us/product/playwright/tags

WORKDIR /code
COPY requirements-playwright.txt /code/

RUN pip install -r requirements-playwright.txt
