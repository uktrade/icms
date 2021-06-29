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
mypy: ## run mypy
	unset UID && .venv/bin/python -m mypy web config

flake8: ## run flake8
	unset UID && .venv/bin/python -m flake8

black: ## run Black in check mode
	unset UID && .venv/bin/python -m black --check .

black_format: ## run Black in reformat mode
	unset UID && .venv/bin/python -m black .

isort: ## run isort in check mode
	unset UID && .venv/bin/python -m isort -j 4 --check .

isort_format: ## run isort in reformat mode
	unset UID && .venv/bin/python -m isort -j 4 .

##@ Development
showmigrations: ## make db migrations
	unset UID && \
	docker-compose run --rm web python ./manage.py showmigrations

migrations: ## make db migrations
	unset UID && \
	docker-compose run --rm web python ./manage.py makemigrations web && \
	docker-compose run --rm web chown "${UID}" web/migrations/*.py

migrate: ## execute db migration
	unset UID && \
	docker-compose run --rm web python ./manage.py migrate

COMMAND="help"
manage: ## execute manage.py
	unset UID && \
	docker-compose run --rm web python ./manage.py ${COMMAND}

add_dummy_data: ## add dummy data
	unset UID && \
	docker-compose run --rm web python ./manage.py add_dummy_data --password admin

add_dummy_application: ## add dummy application
	unset UID && \
	docker-compose run --rm web python ./manage.py add_dummy_application

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

docker_isort: ## run isort in check mode
	unset UID && \
	ICMS_DEBUG=False \
	docker-compose run --rm web python -m isort -j 4 --check .

docker_mypy: ## run mypy
	unset UID && \
	ICMS_DEBUG=False \
	docker-compose run --rm web mypy web config

docker_drop_all_tables: ## drop all tables
	unset UID && \
	docker-compose run --rm web python ./manage.py drop_all_tables --confirm-drop-all-tables

pip-check:
	docker-compose run --rm web pip-check

sqlsequencereset: ## Use this command to generate SQL which will fix cases where a sequence is out of sync with its automatically incremented field data
	unset UID && \
	docker-compose run --rm web python ./manage.py sqlsequencereset web

clean: ## removes python cache files from project
	unset UID && \
	docker-compose run --rm web find . -type d -name __pycache__ -exec rm -rf {} \+

requirements-web: ## install javascript dependencies
	unset UID && \
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose run --rm web sh -c "python manage.py npm && python manage.py collect_npm"

collectstatic: ## copies static files to STATIC_ROOT
	docker-compose run --rm web python ./manage.py collectstatic --noinput --traceback

build: ## build docker containers
	docker-compose pull
	docker-compose build

shell: ## Starts the Python interactive interpreter
	unset UID && \
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose run --rm web python ./manage.py shell -i python

psql: ## Starts psql
	@unset UID && \
	PGPASSWORD=password psql -h localhost -U postgres

# TODO: does this make sense...?
all: requirements-web

local_s3: ## creates s3 buckets on localstack container
	aws --endpoint-url=http://localhost:4572 s3 mb s3://icms.local
	aws --endpoint-url=http://localhost:4572 s3api put-bucket-acl --bucket icms.local --acl public-read

list_s3: ## list S3 bucket contents on localstack container
	aws --endpoint-url=http://localhost:4572 s3 ls s3://icms.local

query_task_result: ## local development tool to query task results
	unset UID && \
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose run --rm web python ./manage.py query_task_result


##@ Server
debug: ## runs system in debug mode
	ICMS_DEBUG=True \
	ICMS_MIGRATE=False \
	docker-compose up

down: ## Stops and downs containers
	docker-compose down --remove-orphans

test: ## run tests (circleci; don't use locally)
	./run-tests.sh --numprocesses 2

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
