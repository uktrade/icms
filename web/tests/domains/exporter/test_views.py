from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.urls import reverse
from guardian.shortcuts import remove_perm
from pytest_django.asserts import assertRedirects

from web.models import Exporter
from web.permissions import Perms
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL


class TestExporterListView(AuthTestCase):
    url = "/exporter/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_admin_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert "Maintain Exporters" in response.content.decode()

    def test_anonymous_post_access_redirects(self):
        response = self.anonymous_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

    def test_forbidden_post_access(self):
        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestExporterListUserView(AuthTestCase):
    url = reverse("user-exporter-list")

    def test_permission(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        exporters = response.context["object_list"]
        assert exporters.count() == 1

        exporter = exporters.first()
        assert exporter == self.exporter


class TestExporterCreateView(AuthTestCase):
    url = "/exporter/create/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    @patch("web.domains.exporter.forms.api_get_company")
    def test_exporter_created(self, api_get_company):
        api_get_company.return_value = {
            "registered_office_address": {
                "address_line_1": "60 rue Wiertz",
                "postcode": "B-1047",
                "locality": "Bruxelles",
            }
        }
        self.ilb_admin_client.post(self.url, {"name": "test exporter", "registered_number": "42"})
        exporter = Exporter.objects.first()
        assert exporter.name == "test exporter"

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert "Create Exporter" in response.content.decode()


class TestEditExporterView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("exporter-edit", kwargs={"pk": self.exporter.id})
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert f"Editing Exporter '{self.exporter.name}'" in response.content.decode()

    def test_edit_agent_forbidden(self, agent_exporter):
        url = reverse("exporter-edit", kwargs={"pk": agent_exporter.id})
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_disabled_fields_when_editing_as_non_org_admin(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        for field in ["name", "registered_number"]:
            assert response.context["form"].fields[field].disabled
            assert (
                response.context["form"].fields[field].help_text
                == "Contact ILB to update this field."
            )


class TestDetailExporterView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("exporter-view", kwargs={"pk": self.importer.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def get_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["object"] == self.exporter
        assert response.context["org_type"] == "exporter"

    def test_post_forbidden(self):
        response = self.ilb_admin_client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestCreateOfficeView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("exporter-office-create", kwargs={"pk": self.exporter.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        exporter = response.context["object"]
        assert exporter == self.exporter

    def test_post(self):
        assert self.exporter.offices.count() == 1
        data = {
            "address_1": "Address line 1",
            "address_2": "Address line 2",
            "address_3": "Address line 3",
            "address_4": "Address line 4",
            "address_5": "Address line 5",
            "postcode": "S1 2SS",  # /PS-IGNORE
        }

        response = self.ilb_admin_client.post(self.url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        assert self.exporter.offices.count() == 2


class TestEditOfficeView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse(
            "exporter-office-edit",
            kwargs={"exporter_pk": self.exporter.id, "office_pk": self.exporter_office.pk},
        )

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        exporter = response.context["object"]
        office = response.context["office"]
        assert exporter == self.exporter
        assert office == self.exporter_office

    def test_post(self):
        data = {
            "address_1": "New Address line 1",
            "address_2": self.exporter_office.address_2,
            "postcode": self.exporter_office.postcode,
        }

        response = self.ilb_admin_client.post(self.url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        self.exporter_office.refresh_from_db()
        assert self.exporter_office.address_1 == "New Address line 1"


class TestArchiveOfficeView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse(
            "exporter-office-archive",
            kwargs={"exporter_pk": self.exporter.id, "office_pk": self.exporter_office.pk},
        )

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.exporter_office.is_active = True
        self.exporter_office.save()
        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.exporter_office.refresh_from_db()
        assert not self.exporter_office.is_active

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestUnarchiveOfficeView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse(
            "exporter-office-unarchive",
            kwargs={"exporter_pk": self.exporter.id, "office_pk": self.exporter_office.pk},
        )
        self.exporter_office.is_active = False
        self.exporter_office.save()

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.exporter_office.is_active = False
        self.exporter_office.save()
        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.exporter_office.refresh_from_db()
        assert self.exporter_office.is_active

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestCreateAgentView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("exporter-agent-create", kwargs={"exporter_pk": self.exporter.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["object"] == self.exporter

    def test_post(self):
        assert self.exporter.agents.count() == 1

        data = {
            "main_exporter": self.exporter.pk,
            "name": "Exporter one new agent",
            "registered_number": "123456789",
        }

        response = self.ilb_admin_client.post(self.url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        assert self.exporter.agents.count() == 2


class TestEditAgentView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.exporter_agent = self.exporter.agents.first()
        self.url = reverse("exporter-agent-edit", kwargs={"pk": self.exporter_agent.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["object"] == self.exporter
        assert response.context["org_type"] == "exporter"
        assert response.context["can_manage_contacts"]

    def test_post(self):
        data = {
            "main_exporter": self.exporter.pk,
            "name": "Exporter one new agent",
            "registered_number": "1234567890",
        }

        response = self.ilb_admin_client.post(self.url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        self.exporter_agent.refresh_from_db()
        assert self.exporter_agent.registered_number == "1234567890"

    def test_disabled_fields_when_editing_as_non_org_admin(self):
        response = self.exporter_agent_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        for field in ["name", "registered_number"]:
            assert response.context["form"].fields[field].disabled
            assert (
                response.context["form"].fields[field].help_text
                == "Contact ILB to update this field."
            )


class TestArchiveAgentView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.exporter_agent = self.exporter.agents.first()
        self.url = reverse("exporter-agent-archive", kwargs={"pk": self.exporter_agent.id})

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.exporter_agent.refresh_from_db()
        assert not self.exporter_agent.is_active

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestUnarchiveAgentView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.exporter_agent = self.exporter.agents.first()
        self.exporter_agent.is_active = False
        self.exporter_agent.save()

        self.url = reverse("exporter-agent-unarchive", kwargs={"pk": self.exporter_agent.id})

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.exporter_agent.refresh_from_db()
        assert self.exporter_agent.is_active

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestEditUserExporterPermissionsView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse(
            "edit-user-exporter-permissions",
            kwargs={"org_pk": self.exporter.id, "user_pk": self.exporter_user.id},
        )

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        #
        # Removing the manage permission should cause the importer user to be forbidden
        #
        remove_perm(
            Perms.obj.exporter.manage_contacts_and_agents, self.exporter_user, self.exporter
        )
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["page_title"] == "Edit Exporter user permissions"
        assert response.context["org_type"] == "Exporter"
        assert response.context["contact"] == self.exporter_user
        assert response.context["organisation"] == self.exporter

    def test_post(self):
        data = {
            "permissions": [
                Perms.obj.exporter.edit.codename,
                Perms.obj.exporter.manage_contacts_and_agents.codename,
            ]
        }
        response = self.ilb_admin_client.post(self.url, data)

        assert response.status_code == HTTPStatus.FOUND

        self.exporter_user.refresh_from_db()

        perms = self.exporter_user.get_all_permissions(self.exporter)
        assert perms == {
            Perms.obj.exporter.edit.codename,
            Perms.obj.exporter.manage_contacts_and_agents.codename,
        }
