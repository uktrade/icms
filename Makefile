# Default command
.DEFAULT_GOAL := help

# Simply by being mentioned as a target, this tells make to export all variables to child processes by default.
.EXPORT_ALL_VARIABLES:

# https://docs.docker.com/compose/reference/envvars/#compose_project_name
COMPOSE_PROJECT_NAME=icms

# TODO: understand what this is for and whether it's still needed
UID=$(shell id -u):$(shell id -g)

##@ Help
help: ## Show this screen
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Local
mypy: ## run mypy
	unset UID && .venv/bin/python -m mypy --config-file=pyproject.toml web data_migration config ${args}

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

format: isort_format black_format
check: flake8 black isort mypy

##@ Development
showmigrations: ## make db migrations
	unset UID && \
	docker-compose run --rm web python ./manage.py showmigrations

migrations: ## make db migrations
	unset UID && \
	docker-compose run --rm web python ./manage.py makemigrations web && \
	docker-compose run --rm web chown "${UID}" web/migrations/*.py

data_migrations: ## make data_migration migrations
	unset UID && \
	docker-compose run --rm web python ./manage.py makemigrations data_migration && \
	docker-compose run --rm web chown "${UID}" data_migration/migrations/*.py

check_migrations: ## Check for missing migrations:
	unset UID && \
	docker-compose run --no-TTY --rm web python ./manage.py makemigrations --check --dry-run --settings=config.settings.local

migrate: ## execute db migration
	unset UID && \
	docker-compose run --rm web python ./manage.py migrate

check-local: ## run Django check
	unset UID && \
	docker-compose run --rm web python ./manage.py check

check-development: ## run Django check for development environment settings
	unset UID && \
	export DATABASE_URL="unset" && \
	export ICMS_ALLOWED_HOSTS="unset" && \
	docker-compose run --rm web python ./manage.py check --settings=config.settings.development

check-staging: ## run Django check for staging environment settings
	unset UID && \
	export DATABASE_URL="unset" && \
	export ICMS_ALLOWED_HOSTS="unset" && \
	docker-compose run --rm web python ./manage.py check --settings=config.settings.staging

check-staging-with-deploy: ## run Django check for staging environment settings with deploy flag
	unset UID && \
	export DATABASE_URL="unset" && \
	docker-compose run --rm web python ./manage.py check --deploy --settings=config.settings.staging

manage: ## execute manage.py
	unset UID && \
	docker-compose run --rm web python ./manage.py ${args}

add_dummy_data: ## add dummy data
	unset UID && \
	docker-compose run --rm web python ./manage.py add_dummy_data --password admin

##@ Docker
setup: ## sets up system for first use
	scripts/initial-setup.sh
	make migrations migrate

docker_flake8: ## run flake8
	unset UID && \
	docker-compose run --rm web python -m flake8

docker_black: ## run Black in check mode
	unset UID && \
	docker-compose run --rm web python -m black --check .

docker_isort: ## run isort in check mode
	unset UID && \
	docker-compose run --rm web python -m isort -j 4 --check .

docker_mypy: ## run mypy
	unset UID && \
	docker-compose run --rm web mypy --config-file=pyproject.toml web data_migration config

docker_drop_all_tables: ## drop all tables
	unset UID && \
	docker-compose run --rm web python ./manage.py drop_all_tables --confirm-drop-all-tables

pip-check:
	docker-compose run --rm web pip-check

pip-tree:
	docker-compose run --rm web pipdeptree ${args}

sqlsequencereset: ## Use this command to generate SQL which will fix cases where a sequence is out of sync with its automatically incremented field data
	unset UID && \
	docker-compose run --rm web python ./manage.py sqlsequencereset web

clean: ## removes python cache files from project
	unset UID && \
	docker-compose run --rm web find . -type d -name __pycache__ -exec rm -rf {} \+

requirements-web: ## install javascript dependencies
	unset UID && \
	docker-compose run --rm web sh -c "python manage.py npm && python manage.py collect_npm"

collectstatic: ## copies static files to STATIC_ROOT
	docker-compose run --rm web python ./manage.py collectstatic --noinput --traceback

build: ## build docker containers
	docker-compose pull
	docker-compose build

shell: ## Starts the Python interactive interpreter
	unset UID && \
	docker-compose run --rm web python ./manage.py shell -i python ${args}

psql: ## Starts psql
	@unset UID && \
	PGPASSWORD=password psql -p 6000 -h localhost -U postgres

# TODO: does this make sense...?
all: requirements-web

local_s3: ## creates s3 buckets on localstack container
	aws --endpoint-url=http://localhost:4566 s3 mb s3://icms.local
	aws --endpoint-url=http://localhost:4566 s3api put-bucket-acl --bucket icms.local --acl public-read

list_s3: ## list S3 bucket contents on localstack container
	aws --endpoint-url=http://localhost:4566 s3 ls s3://icms.local --human-readable

query_task_result: ## local development tool to query task results
	unset UID && \
	docker-compose run --rm web python ./manage.py query_task_result

##@ Test
test: ## run tests (circleci; don't use locally as it produces a coverage report)
	./run-tests.sh \
		--cov=web \
		--cov=config \
		--cov-report xml:test-reports/cov.xml \
		--maxprocesses=2 \
		--cov-fail-under 77 ${args}

migration_test: ## Run data migration tests
	./run-tests.sh data_migration --create-db --numprocesses 2 ${args}


end_to_end_clear_session: ## Clears the session cookies stored after running end to end tests
	rm -f importer_user.json && \
	rm -f exporter_user.json && \
	rm -f ilb_admin.json

end_to_end_test: ## Run end to end tests in a container
	docker-compose run -it --rm playwright-runner pytest -c playwright/pytest.ini web/end_to_end/ --numprocesses=auto ${args} && \
	make end_to_end_clear_session


end_to_end_test_firearm_chief: ## Ran to send applications to icms-hmrc
	docker-compose run -it --rm playwright-runner pytest -c playwright/pytest.ini web/end_to_end/ -k test_can_create_fa_ --numprocesses 3 ${args} && \
	make end_to_end_clear_session


end_to_end_test_local: ## Run end to end tests locally
	.venv/bin/python -m pytest -c playwright/pytest.ini web/end_to_end/ ${args} && \
	make end_to_end_clear_session

create_end_to_end_caseworker: ## Create an end to end test using codegen for the caseworker site
	.venv/bin/python -m playwright codegen http://caseworker:8080/ --target python-pytest --viewport-size "1920, 1080" ${args}

create_end_to_end_export: ## Create an end to end test using codegen for the exporter site
	.venv/bin/python -m playwright codegen http://export-a-certificate:8080/ --target python-pytest --viewport-size "1920, 1080" ${args}

create_end_to_end_import: ## Create an end to end test using codegen for the importer site
	.venv/bin/python -m playwright codegen http://import-a-licence:8080/ --target python-pytest --viewport-size "1920, 1080" ${args}

##@ Server
debug: ## runs system in debug mode
	docker-compose up -d

down: ## Stops and downs containers
	docker-compose down --remove-orphans
