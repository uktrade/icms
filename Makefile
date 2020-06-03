.DEFAULT_GOAL := help

TEST_TARGET ?= web/tests
.EXPORT_ALL_VARIABLES:

DJANGO_SETTINGS_MODULE=config.settings.development
COMPOSE_PROJECT_NAME=icms

UID=$(shell id -u):$(shell id -g)

##@ Help
help: ## Show this screen
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Development
migrations: ## make db migrations
	unset UID && \
	docker-compose run --rm web python ./manage.py makemigrations ${OPTS}

migrate: ## execute db migration
	unset UID && \
	docker-compose run --rm web python ./manage.py migrate


loaddata: ## Load fixtures
	unset UID && \
	docker-compose run --rm web python ./manage.py loaddata --app web web/fixtures/web/*.json

dumpdata: ## dumps db data
	unset UID && \
	docker-compose run --rm web python ./manage.py dumpdata --format=json web  > test.json

sqlsequencereset: ## Use this command to generate SQL which will fix cases where a sequence is out of sync with its automatically incremented field data
	unset UID && \
	docker-compose run --rm web python ./manage.py sqlsequencereset web

createsuperuser: ## create django super user
	unset UID && \
	docker-compose run --rm web python ./manage.py createsuperuser

clean: ## removes python cache files from project
	unset UID && \
	docker-compose run --rm web find . -type d -name __pycache__ -exec rm -rf {} \+

requirements: ## install dev and prod dependecies via pipenv
	unset UID && \
	docker-compose run --rm web python3 -m pipenv install --dev --system

requirements-web: ## install javascript dependencies
	unset UID && \
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose run --rm web sh -c "python manage.py npm && python manage.py collect-npm"

fixlock: ## install prod dependencies via pipenv
	unset UID && \
	docker-compose run --rm web pipenv install

collectstatic: ## copies static files to STATIC_ROOT
	docker-compose run --rm web python ./manage.py collectstatic --noinput --traceback

build: ## build docker containers
	docker-compose pull
	docker-compose build

shell: ## Starts the Python interactive interpreter
	unset UID && \
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose run --rm web python ./manage.py shell

all: requirements requirements-web

setup: ## sets up system for first use, you might want to run load data after
	make requirements migrations migrate

local_s3: ## creates s3 buckets on localstack container
	aws --endpoint-url=http://localhost:4572 s3 mb s3://icms.local
	aws --endpoint-url=http://localhost:4572 s3api put-bucket-acl --bucket icms.local --acl public-read



##@ Server
debug: ## runs sytem in debug mode
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose up &

run: ## Run with Gunicorn and Whitenoise serving static files
	unset UID && \
	ICMS_SECRET_KEY='prod' \
	DATABASE_URL='postgres://postgres:password@db:5432/postgres' \
	ICMS_ALLOWED_HOSTS='localhost' \
	ICMS_RECAPTCHA_PUBLIC_KEY='6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI' \
	ICMS_RECAPTCHA_PRIVATE_KEY='6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe' \
	ICMS_EMAIL_FROM='prod@example.com' \
	ICMS_ADDRESS_API_KEY='prod' \
	ICMS_SILENCED_SYSTEM_CHECKS='captcha.recaptcha_test_key_error' \
	AWS_SES_ACCESS_KEY_ID='prod' \
	AWS_SES_SECRET_ACCESS_KEY='prod' \
	ELASTIC_APM_ENVIRONMENT='prod-test' \
	ELASTIC_APM_URL='https://apm.ci.uktrade.io' \
	DJANGO_SETTINGS_MODULE=config.settings.production \
	docker-compose up

down: ## Stops and downs containers
	docker-compose down

##@ Tests & Reports
flake8: ## runs lint tests
	unset UID && \
	ICMS_DEBUG=False \
	docker-compose run --rm web python -m flake8

test: ## run tests
	mkdir -p test-reports
	unset UID && \
	ICMS_DEBUG=False \
	TEST_TARGET='web/tests' \
	DJANGO_SETTINGS_MODULE=config.settings.test \
	docker-compose run --rm web python -m pytest -p no:sugar --cov=web --cov=config --cov-report xml:test-reports/cov.xml $(TEST_TARGET)

accessibility: ## Generate accessibility reports
	unset UID && \
	docker-compose run --rm pa11y node index.js


behave: down ## runs functional tests
	# recreate test database
	docker-compose run --rm web sh -c "echo 'drop  database test_postgres; create database test_postgres;' | python manage.py dbshell"

	# start containers
	DATABASE_URL='postgres://postgres:password@db:5432/test_postgres' \
	ICMS_DEBUG=True \
	docker-compose up -d

	# load fixtures for intial data on test database
	docker-compose exec web sh -c " \
		DATABASE_URL='postgres://postgres:password@db:5432/test_postgres' \
		python manage.py loaddata features/fixtures/initial-data.json \
	"

	# keep db as postgres since behave will prepend test_ to db when selectiong one to use
	docker-compose exec web sh -c " \
		dockerize -wait http://localhost:8080 -timeout 60s && \
		DJANGO_SETTINGS_MODULE=config.settings.test \
		DATABASE_URL='postgres://postgres:password@db:5432/postgres' \
		python manage.py behave --keepdb $(BEHAVE_OPTS)\
	"

	docker-compose down


##@ Releases

release_major: ## create major release
	./scripts/release.sh major

release_minor: ## create minor release
	./scripts/release.sh minor

release_patch: ## create patch release
	./scripts/release.sh patch

