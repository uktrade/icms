requirements:
	pip install -r requirements.txt

collectstatic:
	./manage.py collectstatic --noinput --traceback

build:
	docker-compose build web

debug:
	ICMS_DEBUG=True docker-compose up

run: collectstatic
	ICMS_DEBUG=False docker-compose up

release_major:
	./scripts/release.sh major

release_minor:
	./scripts/release.sh minor

release_patch:
	./scripts/release.sh patch

all: requirements
