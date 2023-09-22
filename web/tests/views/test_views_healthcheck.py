from unittest.mock import patch

import pytest
from django.urls import reverse

import web.views.views_healthcheck as views_healthcheck


@pytest.fixture
def healthcheck_url():
    return reverse("health-check")


def test_healthcheck_ok(db, cw_client, healthcheck_url):
    response = cw_client.get(healthcheck_url)

    assert response.status_code == 200
    assert "<status>OK</status>" in str(response.content)
    assert response.headers["content-type"] == "text/xml"


def test_healthcheck_fail(db, cw_client, healthcheck_url):
    def failing_check():
        return views_healthcheck.CheckResult(success=False)

    def dummy_get_services():
        return (failing_check,)

    with patch("web.views.views_healthcheck.get_services_to_check", dummy_get_services):
        response = cw_client.get(healthcheck_url)

    assert response.status_code == 500
    assert "<status>FALSE</status>" in str(response.content)
    assert response.headers["content-type"] == "text/xml"
