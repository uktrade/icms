from http import HTTPStatus

import pytest
from django.test.client import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import Exporter, Importer, User
from web.permissions import organisation_get_contacts
from web.tests.auth.auth import AuthTestCase


class TestAddOrgContactView(AuthTestCase):
    def test_ilb_admin_can_add(self):
        add_user_to_org(self.ilb_admin_client, self.exporter_user, "importer", self.importer)
        add_user_to_org(self.ilb_admin_client, self.exporter_user, "importer", self.importer_agent)
        add_user_to_org(self.ilb_admin_client, self.importer_user, "exporter", self.exporter)
        add_user_to_org(self.ilb_admin_client, self.importer_user, "exporter", self.exporter_agent)

    def test_importer_contact_can_add(self):
        add_user_to_org(self.importer_client, self.exporter_user, "importer", self.importer)
        add_user_to_org(self.importer_client, self.exporter_user, "importer", self.importer_agent)

        # Test exporter add forbidden for importer user
        url = reverse("contacts:add", kwargs={"org_type": "exporter", "org_pk": self.exporter.pk})
        form_data = {"contact": self.importer_user.pk}

        response = self.importer_client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_exporter_contact_can_add(self):
        add_user_to_org(self.exporter_client, self.importer_user, "exporter", self.exporter)
        add_user_to_org(self.exporter_client, self.importer_user, "exporter", self.exporter_agent)

        # Test importer add forbidden for exporter user
        url = reverse("contacts:add", kwargs={"org_type": "importer", "org_pk": self.importer.pk})
        form_data = {"contact": self.exporter_user.pk}

        response = self.exporter_client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestDeleteOrgContactView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        """Ensure each org has multiple users to later remove."""
        add_user_to_org(self.ilb_admin_client, self.exporter_user, "importer", self.importer)
        add_user_to_org(self.ilb_admin_client, self.exporter_user, "importer", self.importer_agent)
        add_user_to_org(self.ilb_admin_client, self.importer_user, "exporter", self.exporter)
        add_user_to_org(self.ilb_admin_client, self.importer_user, "exporter", self.exporter_agent)

    def test_ilb_admin_can_remove(self):
        remove_user_from_org(self.ilb_admin_client, self.exporter_user, "importer", self.importer)
        remove_user_from_org(
            self.ilb_admin_client, self.exporter_user, "importer", self.importer_agent
        )
        remove_user_from_org(self.ilb_admin_client, self.importer_user, "exporter", self.exporter)
        remove_user_from_org(
            self.ilb_admin_client, self.importer_user, "exporter", self.exporter_agent
        )

    def test_importer_contact_can_remove(self):
        remove_user_from_org(self.importer_client, self.exporter_user, "importer", self.importer)
        remove_user_from_org(
            self.importer_client, self.exporter_user, "importer", self.importer_agent
        )

        # Test exporter delete forbidden for importer user
        url = reverse(
            "contacts:delete",
            kwargs={
                "org_type": "exporter",
                "org_pk": self.exporter.pk,
                "contact_pk": self.importer_user.pk,
            },
        )

        response = self.importer_client.post(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_exporter_contact_can_add(self):
        remove_user_from_org(self.exporter_client, self.importer_user, "exporter", self.exporter)
        remove_user_from_org(
            self.exporter_client, self.importer_user, "exporter", self.exporter_agent
        )

        # Test importer delete forbidden for exporter user
        url = reverse(
            "contacts:delete",
            kwargs={
                "org_type": "importer",
                "org_pk": self.importer.pk,
                "contact_pk": self.exporter_user.pk,
            },
        )

        response = self.exporter_client.post(url)
        assert response.status_code == HTTPStatus.FORBIDDEN


def add_user_to_org(client: Client, user: User, org_type: str, org: Importer | Exporter) -> None:
    org_contacts = organisation_get_contacts(org)
    assert not org_contacts.contains(user)

    url = reverse("contacts:add", kwargs={"org_type": org_type, "org_pk": org.pk})

    form_data = {"contact": user.pk}

    response = client.post(url, data=form_data)
    if org.is_agent():
        assertRedirects(response, reverse(f"{org_type}-agent-edit", kwargs={"pk": org.pk}))
    else:
        assertRedirects(response, reverse(f"{org_type}-edit", kwargs={"pk": org.pk}))

    org_contacts = organisation_get_contacts(org)
    assert org_contacts.contains(user)


def remove_user_from_org(
    client: Client, user: User, org_type: str, org: Importer | Exporter
) -> None:
    org_contacts = organisation_get_contacts(org)
    assert org_contacts.contains(user)

    url = reverse(
        "contacts:delete", kwargs={"org_type": org_type, "org_pk": org.pk, "contact_pk": user.pk}
    )

    response = client.post(url)
    if org.is_agent():
        assertRedirects(response, reverse(f"{org_type}-agent-edit", kwargs={"pk": org.pk}))
    else:
        assertRedirects(response, reverse(f"{org_type}-edit", kwargs={"pk": org.pk}))

    org_contacts = organisation_get_contacts(org)
    assert not org_contacts.contains(user)
