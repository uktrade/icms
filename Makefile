requirements:
	pip install -r requirements.txt

start:
	python ./manage.py runserver

release-major:
	./scripts/release.sh major

release-minor:
	./scripts/release.sh minor

release-patch:
	./scripts/release.sh patch

all: requirements
