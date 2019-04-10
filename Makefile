requirements:
	docker-compose exec web pip install -r requirements.txt

collectstatic:
	./manage.py collectstatic --noinput --traceback

build:
	docker-compose build web

debug:
	ICMS_DEBUG=True docker-compose up

run: collectstatic
	ICMS_DEBUG=False docker-compose up

migrations:
	docker-compose exec web ./manage.py makemigrations

migrate:
	docker-compose exec web ./manage.py migrate

createsuperuser:
	docker-compose exec web ./manage.py createsuperuser

release_major:
	./scripts/release.sh major

release_minor:
	./scripts/release.sh minor

release_patch:
	./scripts/release.sh patch

shell:
	docker-compose exec web ./manage.py shell

all: requirements
