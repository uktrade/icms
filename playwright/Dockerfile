FROM mcr.microsoft.com/playwright/python:v1.28.0-focal
# Available playwright tags:
#https://mcr.microsoft.com/en-us/product/playwright/tags

WORKDIR /code
COPY requirements-playwright.txt /code/

RUN pip install -r requirements-playwright.txt
