import re

from playwright._repo_version import version


def test_versions_match():
    """Ensure docker version and the installed playwright versions are kept in sync."""
    with open("playwright/Dockerfile") as f:
        line = f.readline()
        match = re.match(r"FROM mcr\.microsoft\.com/playwright/python:v(.+)-jammy", line)
        docker_version = match.group(1)

        assert version == docker_version
