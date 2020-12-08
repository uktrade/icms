.DEFAULT_GOAL := help

TEST_TARGET ?= web/tests
.EXPORT_ALL_VARIABLES:

DJANGO_SETTINGS_MODULE=config.settings.development
COMPOSE_PROJECT_NAME=icms

# TODO: understand what this is for and whether it's still needed
UID=$(shell id -u):$(shell id -g)

##@ Help
help: ## Show this screen
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Local
flake8: ## run flake8
	unset UID && .venv/bin/python -m flake8

black: ## run Black in check mode
	unset UID && .venv/bin/python -m black --check .

black_format: ## run Black in reformat mode
	unset UID && .venv/bin/python -m black .

##@ Development
showmigrations: ## make db migrations
	unset UID && \
	docker-compose run --rm web python ./manage.py showmigrations

migrations: ## make db migrations
	unset UID && \
	docker-compose run --rm web python ./manage.py makemigrations web

migrate: ## execute db migration
	unset UID && \
	docker-compose run --rm web python ./manage.py migrate

COMMAND="help"
manage: ## execute manage.py
	unset UID && \
	docker-compose run --rm web python ./manage.py ${COMMAND}

##@ Docker
setup: ## sets up system for first use
	# doing this here gives it the right permissions, e.g. the local user.
	# that avoids problems with it being owned by root if docker creates it.
	mkdir -p test-reports/bdd-screenshots

	scripts/initial-setup.sh

	make migrations migrate

docker_flake8: ## run flake8
	unset UID && \
	ICMS_DEBUG=False \
	docker-compose run --rm web python -m flake8

docker_black: ## run Black in check mode
	unset UID && \
	ICMS_DEBUG=False \
	docker-compose run --rm web python -m black --check .

mypy: ## run mypy
	unset UID && \
	ICMS_DEBUG=False \
	docker-compose run --rm web mypy web config

pip-check:
	docker-compose run --rm web pip-check

sqlsequencereset: ## Use this command to generate SQL which will fix cases where a sequence is out of sync with its automatically incremented field data
	unset UID && \
	docker-compose run --rm web python ./manage.py sqlsequencereset web

createsuperuser: ## create django super user
	unset UID && \
	docker-compose run --rm web python ./manage.py createsuperuser \
	--username admin --email admin@blaa.com \
	--first_name admin --last_name admin \
	--date_of_birth 2000-1-1 \
	--security_question admin \
	--security_answer admin

clean: ## removes python cache files from project
	unset UID && \
	docker-compose run --rm web find . -type d -name __pycache__ -exec rm -rf {} \+

requirements-web: ## install javascript dependencies
	unset UID && \
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose run --rm web sh -c "python manage.py npm && python manage.py collect-npm"

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

psql: ## Starts psql
	@unset UID && \
	PGPASSWORD=password psql -h localhost -U postgres

# TODO: does this make sense...?
all: requirements-web

local_s3: ## creates s3 buckets on localstack container
	aws --endpoint-url=http://localhost:4572 s3 mb s3://icms.local
	aws --endpoint-url=http://localhost:4572 s3api put-bucket-acl --bucket icms.local --acl public-read

##@ Server
debug: ## runs system in debug mode
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose up

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
	docker-compose down --remove-orphans

test: ## run tests
	./run-tests.sh

accessibility: ## Generate accessibility reports
	unset UID && \
	docker-compose run --rm pa11y node index.js

bdd: ## runs functional tests
	DJANGO_SETTINGS_MODULE=config.settings.test \
	docker-compose exec web sh -c "\
		dockerize -wait tcp://web:8080 -timeout 20s && \
		python manage.py behave ${BEHAVE_OPTS} \
		--no-capture --no-input  --settings=config.settings.test \
		--junit-directory test-reports --junit \
		--tags ~@skip \
	"

##@ Releases

release_major: ## create major release
	./scripts/release.sh major

release_minor: ## create minor release
	./scripts/release.sh minor

release_patch: ## create patch release
	./scripts/release.sh patch
