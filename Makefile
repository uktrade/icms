requirements:
	pip install -r requirements.txt

debug:
	ICMS_DEBUG=True scripts/entry.sh

run:
	ICMS_DEBUG=False scripts/entry.sh

release-major:
	./scripts/release.sh major

release-minor:
	./scripts/release.sh minor

release-patch:
	./scripts/release.sh patch

all: requirements

