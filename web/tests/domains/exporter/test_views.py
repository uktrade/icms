from unittest.mock import patch

import pytest
from django.test import Client

from web.models import Exporter, User
from web.tests.auth import AuthTestCase
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.user.factory import UserFactory

LOGIN_URL = "/"


class ExporterListViewTest(AuthTestCase):
    url = "/exporter/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_access(self):
        self.login()
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_admin_access(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        assert "Maintain Exporters" in response.content.decode()

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_number_of_pages(self):
        ExporterFactory.create_batch(52)

        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        page = response.context_data["page"]
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        ExporterFactory.create_batch(53, is_active=True)
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url + "?page=2")
        page = response.context_data["page"]
        self.assertEqual(len(page.object_list), 5)


class ExporterEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.exporter = ExporterFactory()
        self.url = f"/exporter/{self.exporter.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        assert f"Editing Exporter '{self.exporter.name}'" in response.content.decode()


class ExporterCreateViewTest(AuthTestCase):
    url = "/exporter/create/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @patch("web.domains.exporter.forms.api_get_company")
    def test_exporter_created(self, api_get_company):
        api_get_company.return_value = {
            "registered_office_address": {
                "address_line_1": "60 rue Wiertz",
                "postcode": "B-1047",
                "locality": "Bruxelles",
            }
        }
        self.login_with_permissions(["ilb_admin"])
        self.client.post(self.url, {"name": "test exporter", "registered_number": "42"})
        exporter = Exporter.objects.first()
        self.assertEqual(exporter.name, "test exporter")

    def test_page_title(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        assert "Create Exporter" in response.content.decode()


def test_detail_exporter_anonymous_user():
    client = Client()
    response = client.get("/exporter/1/")
    assert response.status_code == 302
    assert response["Location"] == "/?next=/exporter/1/"


@pytest.mark.django_db
def test_detail_exporter_permission_not_ok():
    user = UserFactory.create(
        is_active=True, account_status=User.ACTIVE, password_disposition=User.FULL
    )

    client = Client()
    client.login(username=user.username, password="test")
    response = client.get("/exporter/1/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_detail_exporter_ok():
    ilb_admin = UserFactory.create(
        is_active=True,
        account_status=User.ACTIVE,
        password_disposition=User.FULL,
        permission_codenames=["ilb_admin"],
    )
    exporter = ExporterFactory.create(is_active=True)

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.get(f"/exporter/{ exporter.pk }/")

    assert response.status_code == 200
    assert exporter.name in response.content.decode()
