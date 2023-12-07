from http import HTTPStatus
from unittest import mock

import pytest
from django.test.client import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import (
    Exporter,
    ExporterContactInvite,
    Importer,
    ImporterContactInvite,
    User,
)
from web.permissions import organisation_get_contacts
from web.tests.auth.auth import AuthTestCase


class TestAddOrgContactView(AuthTestCase):
    def test_ilb_admin_can_add(self):
        add_user_to_org(self.ilb_admin_client, self.exporter_user, "importer", self.importer)
        add_user_to_org(self.ilb_admin_client, self.exporter_user, "importer", self.importer_agent)
        add_user_to_org(self.ilb_admin_client, self.importer_user, "exporter", self.exporter)
        add_user_to_org(self.ilb_admin_client, self.importer_user, "exporter", self.exporter_agent)

    def test_importer_contact_can_not_add(self):
        url = reverse("contacts:add", kwargs={"org_type": "importer", "org_pk": self.importer.pk})
        form_data = {"contact": self.exporter_user.pk}
        response = self.importer_client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FORBIDDEN

        url = reverse("contacts:add", kwargs={"org_type": "exporter", "org_pk": self.exporter.pk})
        form_data = {"contact": self.importer_user.pk}

        response = self.importer_client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_exporter_contact_can_not_add(self):
        url = reverse("contacts:add", kwargs={"org_type": "exporter", "org_pk": self.exporter.pk})
        form_data = {"contact": self.importer_user.pk}

        response = self.exporter_client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FORBIDDEN

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

    def test_importer_contact_can_not_remove(self):
        url = reverse(
            "contacts:delete",
            kwargs={
                "org_type": "importer",
                "org_pk": self.importer.pk,
                "contact_pk": self.exporter_user.pk,
            },
        )

        response = self.importer_client.post(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

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

    def test_exporter_contact_can_not_remove(self):
        url = reverse(
            "contacts:delete",
            kwargs={
                "org_type": "exporter",
                "org_pk": self.exporter.pk,
                "contact_pk": self.importer_user.pk,
            },
        )

        response = self.exporter_client.post(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

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


class TestInviteOrgContactView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer_invite_url = reverse(
            "contacts:invite-org-contact",
            kwargs={"org_type": "importer", "org_pk": self.importer.pk},
        )

        self.exporter_invite_url = reverse(
            "contacts:invite-org-contact",
            kwargs={"org_type": "exporter", "org_pk": self.exporter.pk},
        )

    def test_permission(self):
        response = self.importer_client.get(self.importer_invite_url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.get(self.importer_invite_url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.importer_invite_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.exporter_invite_url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.get(self.exporter_invite_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.exporter_invite_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.importer_client.get(self.importer_invite_url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["page_title"] == "Invite an Importer Contact"
        assert response.context["organisation"] == "Importer"

        response = self.exporter_client.get(self.exporter_invite_url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["page_title"] == "Invite an Exporter Contact"
        assert response.context["organisation"] == "Exporter"

    @mock.patch("web.domains.contacts.views.send_org_contact_invite_email", autospec=True)
    def test_post_success_importer_invite(self, mock_send_org_contact_invite_email):
        form_data = {
            "email": "user@example.com",  # /PS-IGNORE
            "first_name": "Bobs",
            "last_name": "Burgers",
        }

        response = self.importer_client.post(self.importer_invite_url, form_data)
        assertRedirects(response, reverse("importer-edit", kwargs={"pk": self.importer.pk}))

        invite = ImporterContactInvite.objects.first()
        assert mock_send_org_contact_invite_email.call_args == mock.call(self.importer, invite)

        assert invite.invited_by == self.importer_user
        assert invite.email == "user@example.com"  # /PS-IGNORE
        assert invite.first_name == "Bobs"
        assert invite.last_name == "Burgers"
        assert not invite.processed

    @mock.patch("web.domains.contacts.views.send_org_contact_invite_email", autospec=True)
    def test_post_success_exporter_invite(self, mock_send_org_contact_invite_email):
        form_data = {
            "email": "user@example.com",  # /PS-IGNORE
            "first_name": "Bobs",
            "last_name": "Burgers",
        }

        response = self.exporter_client.post(self.exporter_invite_url, form_data)
        assertRedirects(response, reverse("exporter-edit", kwargs={"pk": self.exporter.pk}))

        invite = ExporterContactInvite.objects.first()
        assert mock_send_org_contact_invite_email.call_args == mock.call(self.exporter, invite)

        assert invite.invited_by == self.exporter_user
        assert invite.email == "user@example.com"  # /PS-IGNORE
        assert invite.first_name == "Bobs"
        assert invite.last_name == "Burgers"
        assert not invite.processed

    @mock.patch("web.domains.contacts.views.send_org_contact_invite_email", autospec=True)
    def test_post_success_update_existing_invite(self, mock_send_org_contact_invite_email):
        form_data = {
            "email": "user@example.com",  # /PS-IGNORE
            "first_name": "Bobs",
            "last_name": "Burgers",
        }

        # Create an invite for the user.
        invite = ImporterContactInvite.objects.create(
            invited_by=self.importer_user, organisation=self.importer, **form_data
        )
        invite.first_name = "Not Bob"
        invite.save()

        response = self.importer_client.post(self.importer_invite_url, form_data)
        assertRedirects(response, reverse("importer-edit", kwargs={"pk": self.importer.pk}))

        invite.refresh_from_db()
        assert mock_send_org_contact_invite_email.call_args == mock.call(self.importer, invite)

        assert invite.invited_by == self.importer_user
        assert invite.email == "user@example.com"  # /PS-IGNORE
        assert invite.first_name == "Bobs"
        assert invite.last_name == "Burgers"
        assert not invite.processed

    def test_post_fail_for_existing_contact(self):
        form_data = {
            "email": self.importer_user.email,
            "first_name": self.importer_user.first_name,
            "last_name": self.importer_user.last_name,
        }
        response = self.importer_client.post(self.importer_invite_url, form_data)
        assert response.status_code == HTTPStatus.OK

        messages = list(response.context["messages"])
        error_msg = str(messages[0])

        assert error_msg == "User with that email is already a contact."


class TestAcceptOrgContactInviteView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        # Invite the exporter user to the importer
        importer_invite = ImporterContactInvite.objects.create(
            invited_by=self.importer_user,
            organisation=self.importer,
            email=self.exporter_user.email,
            first_name=self.exporter_user.first_name,
            last_name=self.exporter_user.last_name,
        )

        # Invite the importer user to the exporter
        exporter_invite = ExporterContactInvite.objects.create(
            invited_by=self.exporter_user,
            organisation=self.exporter,
            email=self.importer_user.email,
            first_name=self.importer_user.first_name,
            last_name=self.importer_user.last_name,
        )
        self.accept_importer_invite_url = reverse(
            "contacts:accept-org-invite", kwargs={"code": importer_invite.code}
        )

        self.accept_exporter_invite_url = reverse(
            "contacts:accept-org-invite", kwargs={"code": exporter_invite.code}
        )

    def test_permission(self):
        """A user can only accept invites matching their user."""

        response = self.importer_client.get(self.accept_exporter_invite_url)
        assert response.status_code == HTTPStatus.OK
        response = self.importer_client.get(self.accept_importer_invite_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.accept_importer_invite_url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.accept_exporter_invite_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.importer_client.get(self.accept_exporter_invite_url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["invited_by"] == self.exporter_user.full_name
        assert response.context["organisation_name"] == self.exporter.name

        response = self.exporter_client.get(self.accept_importer_invite_url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["invited_by"] == self.importer_user.full_name
        assert response.context["organisation_name"] == self.importer.display_name

    def test_post_success_accept_invite(self):
        form_data = {"accept_invite": "True"}

        response = self.importer_client.post(self.accept_exporter_invite_url, data=form_data)
        assertRedirects(response, reverse("workbasket"))

        # Check the importer user is now an exporter org contact
        assert self.importer_user in organisation_get_contacts(self.exporter)

        response = self.exporter_client.post(self.accept_importer_invite_url, data=form_data)
        assertRedirects(response, reverse("workbasket"))

        # Check the exporter user is now an importer org contact
        assert self.exporter_user in organisation_get_contacts(self.importer)

    def test_post_success_reject_invite(self):
        form_data = {"accept_invite": "False"}

        response = self.importer_client.post(self.accept_exporter_invite_url, data=form_data)
        assertRedirects(response, reverse("workbasket"))

        # Check the importer user is now an exporter org contact
        assert self.importer_user not in organisation_get_contacts(self.exporter)

        response = self.exporter_client.post(self.accept_importer_invite_url, data=form_data)
        assertRedirects(response, reverse("workbasket"))

        # Check the exporter user is now an importer org contact
        assert self.exporter_user not in organisation_get_contacts(self.importer)
