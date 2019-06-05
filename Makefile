.EXPORT_ALL_VARIABLES:
DJANGO_SETTINGS_MODULE=config.settings.development

UID=$(shell id -u):$(shell id -g)

clean:
	unset UID && \
	docker-compose run web find . -type d -name __pycache__ -exec rm -rf {} \+

requirements:
	unset UID && \
	docker-compose run web python3 -m pipenv install --dev --system

collectstatic:
	docker-compose run web ./manage.py collectstatic --noinput --traceback

build:
	docker-compose build web

debug:
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose up

# Run with Gunicorn and Whitenoise serving static files
run: test
	DJANGO_SETTINGS_MODULE=config.settings.production \
	ICMS_DEBUG=False \
	docker-compose up

test: clean
	DJANGO_SETTINGS_MODULE=config.settings.test \
	docker-compose run web pytest -s --verbose --cov=web --cov=config web/tests

# Generate accessibility reports
accessibility:
	unset UID && \
	docker-compose run pa11y node index.js

test_style: clean
	DJANGO_SETTINGS_MODULE=config.settings.test \
	docker-compose run web pytest --flake8

migrations:
	docker-compose run web ./manage.py makemigrations

migrate:
	docker-compose run web ./manage.py migrate

# Load fixtures
loaddata:
	docker-compose run web ./manage.py loaddata --app web web/fixtures/web/*.json

sqlsequencereset:
	docker-compose run web ./manage.py sqlsequencereset web

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
