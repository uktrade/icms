#!/bin/sh -e

echo "Check missing migrations"
python manage.py makemigrations --check --dry-run

echo "Starting server"
python manage.py runserver 0.0.0.0:8080
