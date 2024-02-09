from unittest.mock import patch

from django.urls import reverse


def test_healthcheck_ok(cw_client):
    def passing_check():
        return True

    def dummy_get_services():
        return [passing_check]

    with patch("web.views.views_healthcheck.get_services_to_check", dummy_get_services):
        response = cw_client.get(reverse("health-check"))

    assert response.status_code == 200
    assert "<status>OK</status>" in str(response.content)
    assert response.headers["content-type"] == "text/xml"


def test_healthcheck_fail(cw_client):
    def failing_check():
        return False

    def dummy_get_services():
        return [failing_check]

    with patch("web.views.views_healthcheck.get_services_to_check", dummy_get_services):
        response = cw_client.get(reverse("health-check"))

    assert response.status_code == 500
    assert "<status>FALSE</status>" in str(response.content)
    assert "<!--The following check failed: failing_check-->" in str(response.content)
    assert response.headers["content-type"] == "text/xml"
