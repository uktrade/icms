.EXPORT_ALL_VARIABLES:
DJANGO_SETTINGS_MODULE=config.settings.development

UID=$(shell id -u):$(shell id -g)

clean:
	unset UID && \
	docker-compose run web find . -type d -name __pycache__ -exec rm -rf {} \+

requirements:
	unset UID && \
	docker-compose run web python3 -m pipenv install --dev --system
#	docker-compose run web pipenv install

collectstatic:
	docker-compose run web ./manage.py collectstatic --noinput --traceback

build:
	docker-compose build web

debug:
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose up

# Run with Gunicorn and Whitenoise serving static files
run: 
	ICMS_SECRET_KEY='prod' \
	DATABASE_URL='postgres://postgres@db:5432/postgres' \
	ICMS_ALLOWED_HOSTS='localhost' \
	ICMS_RECAPTCHA_PUBLIC_KEY='6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI' \
	ICMS_RECAPTCHA_PRIVATE_KEY='6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe' \
	ICMS_EMAIL_FROM='prod@example.com' \
	ICMS_ADDRESS_API_KEY='prod' \
	ICMS_SILENCED_SYSTEM_CHECKS='captcha.recaptcha_test_key_error' \
	AWS_ACCESS_KEY_ID='prod' \
	AWS_SECRET_ACCESS_KEY='prod' \
	DJANGO_SETTINGS_MODULE=config.settings.production \
	docker-compose up

test: clean
	ICMS_DEBUG=False \
	TEST_TARGET='web/tests' \
	DJANGO_SETTINGS_MODULE=config.settings.test \
	docker-compose run web pytest -s --verbose --cov=web --cov=config $(TEST_TARGET)

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

dumpdata:
	docker-compose run web ./manage.py dumpdata --format=json web  > test.json

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
