.EXPORT_ALL_VARIABLES:
DJANGO_SETTINGS_MODULE=config.settings.development
# Current user used in docker-compose.yml
UID=$(shell id -u):$(shell id -g)

clean:
	docker-compose run web find . -type d -name __pycache__ -exec rm -r {} \+

requirements:
	docker-compose run web pip install --user -r requirements.txt

collectstatic:
	docker-compose run web ./manage.py collectstatic --noinput --traceback

build:
	docker-compose build web

debug:
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose up

# Run with Gunicorn and Whitenoise serving static files
run: clean test collectstatic
	ICMS_DEBUG=False \
	docker-compose up

test: clean requirements
	DJANGO_SETTINGS_MODULE=config.settings.test \
	docker-compose run web py.test -s --verbose --cov=web --cov=config web/tests

# Generate accessibility reports
accessibility:
	docker-compose run pa11y node index.js

test_style: clean
	DJANGO_SETTINGS_MODULE=config.settings.test \
	docker-compose run web pytest --flake8

migrations:
	docker-compose run web ./manage.py makemigrations

migrate:
	docker-compose run web ./manage.py migrate

createsuperuser:
	docker-compose run web ./manage.py createsuperuser

release_major:
	./scripts/release.sh major

release_minor:
	./scripts/release.sh minor

release_patch:
	./scripts/release.sh patch

shell:
	docker-compose run web ./manage.py shell

all: requirements
