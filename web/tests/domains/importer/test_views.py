from http import HTTPStatus
from unittest.mock import create_autospec, patch
from urllib.parse import urljoin

import freezegun
import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import remove_perm
from pytest_django.asserts import assertInHTML, assertRedirects

from web.domains.importer import views
from web.mail.constants import EmailTypes
from web.models import Importer, Section5Authority
from web.permissions import Perms
from web.sites import get_caseworker_site_domain
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.helpers import (
    check_gov_notify_email_was_sent,
    get_messages_from_response,
)
from web.utils.s3 import get_file_from_s3


class TestImporterListAdminView(AuthTestCase):
    url = reverse("importer-list")
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_admin_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_external_user_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_constabulary_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "Maintain Importers"

    def test_anonymous_post_access_redirects(self):
        response = self.anonymous_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

    def test_forbidden_post_access(self):
        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_number_of_pages(self):
        # Create 58 importer as paging lists 50 items per page
        for i in range(58):
            ImporterFactory()

        response = self.ilb_admin_client.get(self.url, {"name": ""})
        page = response.context_data["page"]
        assert page.paginator.num_pages == 2

    def test_page_results(self):
        for i in range(50):
            ImporterFactory(is_active=True)

        response = self.ilb_admin_client.get(self.url, {"page": "2", "name": ""})
        page = response.context_data["page"]

        # We have added three to use as a pytest fixture
        assert len(page.object_list) == 3


class TestImporterListUserView(AuthTestCase):
    url = reverse("user-importer-list")

    def test_permission(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        importers = response.context["object_list"]
        assert importers.count() == 1

        importer = importers.first()
        assert importer == self.importer


class TestImporterListRegulatorView(AuthTestCase):
    url = reverse("regulator-importer-list")

    @pytest.fixture(autouse=True)
    def setup(self, _setup, ho_admin_client, nca_admin_client, constabulary_client):
        self.ho_admin_client = ho_admin_client
        self.nca_admin_client = nca_admin_client
        self.constabulary_client = constabulary_client

    def test_permission(self):
        response = self.ho_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.nca_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.constabulary_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ho_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        print(response.context)

        assert response.context["page_title"] == "Maintain Importers"

        importers = response.context["object_list"]
        assert importers.count() == 4


class TestImporterDetailRegulatorView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(
        self, _setup, strict_templates, ho_admin_client, nca_admin_client, constabulary_client
    ):
        self.ho_admin_client = ho_admin_client
        self.nca_admin_client = nca_admin_client
        self.constabulary_client = constabulary_client
        self.url = reverse("regulator-importer-detail", kwargs={"importer_pk": self.importer.id})

    def test_permission(self):
        response = self.ho_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.nca_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.constabulary_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def get_get(self):
        response = self.ho_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["object"] == self.importer
        assert response.context["parent_url"] == reverse("regulator-importer-list")
        assert response.context["show_section5_authorities"]

    def test_post_forbidden(self):
        response = self.ho_admin_client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestIndividualImporterCreateView(AuthTestCase):
    url = reverse("importer-create", kwargs={"entity_type": "individual"})
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_importer_created(self):
        data = {
            "eori_number": "GBPR",
            "user": self.importer_user.pk,
        }
        response = self.ilb_admin_client.post(self.url, data)
        importer = Importer.objects.first()
        assertRedirects(response, reverse("importer-list") + f"?name={importer.name}")
        assert "Importer created successfully." in get_messages_from_response(response)
        assert importer.user == self.importer_user


class TestOrganisationImporterCreateView(AuthTestCase):
    url = reverse("importer-create", kwargs={"entity_type": "organisation"})
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    @patch("web.domains.importer.forms.api_get_company")
    def test_importer_created(self, api_get_company):
        api_get_company.return_value = {
            "registered_office_address": {
                "address_line_1": "60 rue Wiertz",
                "postcode": "B-1047",
                "locality": "Bruxelles",
            }
        }

        data = {
            "eori_number": "GB123456789012345",
            "name": "test importer",
            "registered_number": "42",
        }
        response = self.ilb_admin_client.post(self.url, data)
        importer = Importer.objects.first()
        assertRedirects(response, reverse("importer-list") + f"?name={importer.name}")
        assert importer.name == "test importer", importer


class TestImporterEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer.type = self.importer.INDIVIDUAL
        self.importer.save()
        self.url = reverse("importer-edit", kwargs={"pk": self.importer.id})
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_edit_agent_forbidden(self, agent_importer):
        url = reverse("importer-edit", kwargs={"pk": agent_importer.id})
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        resp_html = response.content.decode("utf-8")

        assertInHTML(f"Editing Importer '{self.importer!s}'", resp_html)

    def test_disabled_fields_when_editing_as_non_org_admin(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        for field in ["user", "eori_number"]:
            assert response.context["form"].fields[field].disabled
            assert (
                response.context["form"].fields[field].help_text
                == "Contact ILB to update this field."
            )

        # Change org type and test again
        self.importer.type = self.importer.ORGANISATION
        self.importer.save()
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        for field in ["registered_number", "name", "eori_number"]:
            assert response.context["form"].fields[field].disabled
            assert (
                response.context["form"].fields[field].help_text
                == "Contact ILB to update this field."
            )

    @patch("web.domains.importer.forms.api_get_company")
    def test_warning_message_displayed_admin_missing_eori_number(self, api_get_company):
        """Tests that a warning message is displayed when the admin user doesn't provide an EORI number."""
        api_get_company.return_value = {
            "registered_office_address": {
                "address_line_1": "60 rue Wiertz",
                "postcode": "B-1047",
                "locality": "Bruxelles",
            }
        }
        self.importer.eori_number = None
        self.importer.save()

        response = self.ilb_admin_client.post(
            self.url,
            data={
                "name": self.importer.name,
                "registered_number": "",
                "eori_number": "",
                "user": self.importer_user.pk,
            },
            follow=True,
        )

        assert response.status_code == HTTPStatus.OK
        messages = list(get_messages(response.wsgi_request))
        message = str(messages[0])
        assert (
            "An EORI number is required to progress an application from this importer, please provide one as soon as possible."
            in message
        )

    def test_prefilled_search_url(self):
        """Tests that the URL to search Importer Access Requests is prefilled with the importer name."""
        response = self.ilb_admin_client.get(self.url)
        resp_html = response.content.decode("utf-8")
        assert f"{reverse('access:importer-list')}?importer_name={self.importer.name}" in resp_html


class TestCreateSection5View(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("importer-section5-create", kwargs={"pk": self.importer.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        importer = response.context["object"]
        assert self.importer == importer

    def test_post(self):
        data = {
            "linked_offices": self.importer_office.pk,
            "reference": "12",
            "postcode": "ox51dw",  # /PS-IGNORE
            "address": "1 Some road Town County",
            "start_date": "01-Dec-2020",
            "end_date": "02-Dec-2020",
            "clausequantity_set-TOTAL_FORMS": 0,
            "clausequantity_set-INITIAL_FORMS": 0,
        }
        response = self.ilb_admin_client.post(self.url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        section5 = Section5Authority.objects.get()
        assert self.importer_office == section5.linked_offices.first()
        assert response["Location"] == reverse("importer-section5-edit", kwargs={"pk": section5.pk})


class TestEditSection5View(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.section5 = Section5Authority.objects.create(importer=self.importer)
        self.url = reverse("importer-section5-edit", kwargs={"pk": self.section5.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        importer = response.context["object"]
        section5 = response.context["section5"]
        assert self.importer == importer
        assert self.section5 == section5


class TestViewSection5View(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.section5 = Section5Authority.objects.create(
            importer=self.importer, start_date=timezone.now().date(), end_date=timezone.now().date()
        )
        self.url = reverse("importer-section5-view", kwargs={"pk": self.section5.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        importer = response.context["object"]
        section5 = response.context["section5"]
        assert self.importer == importer
        assert self.section5 == section5

    def test_post_forbidden(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestArchiveSection5View(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.section5 = Section5Authority.objects.create(
            importer=self.importer,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            reference="Test Section 5 Authority",
        )
        self.url = reverse("importer-section5-archive", kwargs={"pk": self.section5.id})

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    @freezegun.freeze_time("2020-01-01 12:00:00")
    def test_post(self):
        response = self.ilb_admin_client.post(
            self.url,
            data={
                "archive_reason": ["REVOKED", "OTHER", "REFUSED"],
                "other_archive_reason": "Another reason",
            },
        )
        assert response.status_code == HTTPStatus.FOUND

        self.section5.refresh_from_db()
        assert not self.section5.is_active
        check_gov_notify_email_was_sent(
            2,
            ["ilb_admin_two@example.com", "ilb_admin_user@example.com"],  # /PS-IGNORE
            EmailTypes.AUTHORITY_ARCHIVED,
            {
                "reason": "Revoked\r\nRefused",
                "reason_other": "Another reason",
                "authority_name": "Test Section 5 Authority",
                "authority_type": "Section 5",
                "authority_url": urljoin(
                    get_caseworker_site_domain(),
                    reverse("importer-section5-view", kwargs={"pk": self.section5.pk}),
                ),
                "date": "1 January 2020",
                "icms_url": get_caseworker_site_domain(),
                "importer_name": self.importer.name,
                "importer_url": urljoin(
                    get_caseworker_site_domain(),
                    reverse("importer-view", kwargs={"pk": self.importer.pk}),
                ),
            },
        )

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK


class TestUnarchiveSection5View(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.section5 = Section5Authority.objects.create(
            importer=self.importer,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            is_active=False,
        )
        self.url = reverse("importer-section5-unarchive", kwargs={"pk": self.section5.id})

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

        self.section5.refresh_from_db()
        assert self.section5.is_active

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestAddDocumentSection5View(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, document_form_data):
        self.document_form_data = document_form_data
        self.section5 = Section5Authority.objects.create(importer=self.importer)
        self.url = reverse("importer-section5-add-document", kwargs={"pk": self.section5.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        importer = response.context["importer"]
        section5 = response.context["section5"]
        assert self.importer == importer
        assert self.section5 == section5

    def test_post(self):
        assert self.section5.files.count() == 0

        response = self.ilb_admin_client.post(self.url, data=self.document_form_data)
        assert response.status_code == HTTPStatus.FOUND

        assert self.section5.files.count() == 1


class TestViewDocumentSection5View(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, document_form_data, monkeypatch):
        self.section5 = Section5Authority.objects.create(importer=self.importer)
        self.ilb_admin_client.post(
            reverse("importer-section5-add-document", kwargs={"pk": self.section5.id}),
            data=document_form_data,
        )
        self.document = self.section5.files.first()

        self.url = reverse(
            "importer-section5-view-document",
            kwargs={"section5_pk": self.section5.id, "document_pk": self.document.pk},
        )

        get_file_from_s3_mock = create_autospec(get_file_from_s3)
        get_file_from_s3_mock.return_value = b"file_content"
        monkeypatch.setattr(views, "get_file_from_s3", get_file_from_s3_mock)

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.content == b"file_content"
        assert response.headers["Content-Type"] == "text/plain"
        assert (
            response.headers["Content-Disposition"]
            == 'attachment; filename="original_name: myimage.png"'
        )
        assert response.charset == "utf-8"

    def test_post_forbidden(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestDeleteDocumentSection5View(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, document_form_data, monkeypatch):
        self.section5 = Section5Authority.objects.create(importer=self.importer)
        self.ilb_admin_client.post(
            reverse("importer-section5-add-document", kwargs={"pk": self.section5.id}),
            data=document_form_data,
        )
        self.document = self.section5.files.first()

        assert self.document.is_active

        self.url = reverse(
            "importer-section5-delete-document",
            kwargs={"section5_pk": self.section5.id, "document_pk": self.document.pk},
        )

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

        self.document.refresh_from_db()
        assert not self.document.is_active

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestCreateOfficeView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("importer-office-create", kwargs={"pk": self.importer.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        importer = response.context["object"]
        assert importer == self.importer

    def test_post(self):
        assert self.importer.offices.count() == 1
        data = {
            "address_1": "Address line 1",
            "address_2": "Address line 2",
            "address_3": "Address line 3",
            "address_4": "Address line 4",
            "address_5": "Address line 5",
            "postcode": "S1 2SS",  # /PS-IGNORE
            "eori_number": "GB0123456789ABCDE",
        }

        response = self.ilb_admin_client.post(self.url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        assert self.importer.offices.count() == 2

    def test_post_cleans_postcode(self):
        assert self.importer.offices.count() == 1
        data = {
            "address_1": "Address line 1",
            "address_2": "Address line 2",
            "address_3": "Address line 3",
            "address_4": "Address line 4",
            "address_5": "Address line 5",
            "postcode": "s1 2ss",  # /PS-IGNORE
            "eori_number": "GB0123456789ABCDE",
        }

        response = self.ilb_admin_client.post(self.url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        assert self.importer.offices.count() == 2

        latest = self.importer.offices.last()
        # test space stripped and upper case.
        assert latest.postcode == "S12SS"  # /PS-IGNORE


class TestEditOfficeView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse(
            "importer-office-edit",
            kwargs={"importer_pk": self.importer.id, "office_pk": self.importer_office.pk},
        )

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        importer = response.context["object"]
        office = response.context["office"]
        assert importer == self.importer
        assert office == self.importer_office

    def test_post(self):
        data = {
            "address_1": "New Address line 1",
            "address_2": self.importer_office.address_2,
            "postcode": self.importer_office.postcode,
            "eori_number": self.importer_office.eori_number,
        }

        response = self.ilb_admin_client.post(self.url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        self.importer_office.refresh_from_db()
        assert self.importer_office.address_1 == "New Address line 1"


class TestArchiveOfficeView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse(
            "importer-office-archive",
            kwargs={"importer_pk": self.importer.id, "office_pk": self.importer_office.pk},
        )

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.importer_office.is_active = True
        self.importer_office.save()
        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.importer_office.refresh_from_db()
        assert not self.importer_office.is_active

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestUnarchiveOfficeView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse(
            "importer-office-unarchive",
            kwargs={"importer_pk": self.importer.id, "office_pk": self.importer_office.pk},
        )
        self.importer_office.is_active = False
        self.importer_office.save()

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.importer_office.is_active = False
        self.importer_office.save()
        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        self.importer_office.refresh_from_db()
        assert self.importer_office.is_active

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestIndividualAgentCreateView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer.type = self.importer.INDIVIDUAL
        self.importer.save()
        self.url = reverse(
            "importer-agent-create",
            kwargs={"importer_pk": self.importer.id, "entity_type": "individual"},
        )
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_agent_created(self):
        data = {
            "main_importer": self.importer.pk,
            "user": self.importer_user.pk,
        }
        response = self.ilb_admin_client.post(self.url, data)
        agent = Importer.objects.filter(main_importer__isnull=False).first()
        assertRedirects(response, f"/importer/agent/{agent.pk}/edit/")
        assert agent.user == self.importer_user


class TestOrganisationAgentCreateView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer = ImporterFactory()
        self.url = f"/importer/{self.importer.pk}/agent/organisation/create/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_agent_created(self):
        data = {
            "main_importer": self.importer.pk,
            "registered_number": "42",
            "name": "test importer",
        }
        response = self.ilb_admin_client.post(self.url, data)
        agent = Importer.objects.filter(main_importer__isnull=False).first()
        assertRedirects(response, f"/importer/agent/{agent.pk}/edit/")
        assert agent.name == "test importer", agent


class TestAgentEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("importer-agent-edit", kwargs={"pk": self.importer_agent.pk})
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_disabled_fields_when_editing_as_non_org_admin(self):
        response = self.importer_agent_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        for field in ["name", "registered_number"]:
            assert response.context["form"].fields[field].disabled
            assert (
                response.context["form"].fields[field].help_text
                == "Contact ILB to update this field."
            )

        # Change org type and test again
        self.importer_agent.type = self.importer_agent.INDIVIDUAL
        self.importer_agent.save()
        response = self.importer_agent_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        for field in ["user"]:
            assert response.context["form"].fields[field].disabled
            assert (
                response.context["form"].fields[field].help_text
                == "Contact ILB to update this field."
            )

    def test_post(self):
        data = {
            "type": "ORGANISATION",
            "name": self.importer_agent.name,
            "registered_number": "quarante-deux",
            "comments": "Alter agent",
        }
        response = self.ilb_admin_client.post(self.url, data)
        assertRedirects(response, self.url)
        self.importer_agent.refresh_from_db()
        assert self.importer_agent.comments == "Alter agent"
        assert self.importer_agent.registered_number == "quarante-deux"


class TestAgentArchiveView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer.type = self.importer.INDIVIDUAL
        self.importer.save()
        self.agent = ImporterFactory(
            main_importer=self.importer, type=Importer.ORGANISATION, is_active=True
        )

        self.url = f"/importer/agent/{self.agent.pk}/archive/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.post(self.url)
        self.agent.refresh_from_db()
        assert not self.agent.is_active
        assertRedirects(response, f"/importer/{self.importer.pk}/edit/")


class TestAgentUnarchiveView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer.type = self.importer.INDIVIDUAL
        self.importer.save()
        self.agent = ImporterFactory(
            main_importer=self.importer, type=Importer.ORGANISATION, is_active=False
        )

        self.url = f"/importer/agent/{self.agent.pk}/unarchive/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"  #

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.post(self.url)
        self.agent.refresh_from_db()
        assert self.agent.is_active
        assertRedirects(response, f"/importer/{self.importer.pk}/edit/")


class TestImporterDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("importer-view", kwargs={"pk": self.importer.id})

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def get_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["object"] == self.importer
        assert response.context["show_firearm_authorities"]
        assert response.context["show_section5_authorities"]

        #
        # Test importers can't see the firearm and section5 authority sections.
        #
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assert response.context["object"] == self.importer
        assert not response.context["show_firearm_authorities"]
        assert not response.context["show_section5_authorities"]

    def test_post_forbidden(self):
        response = self.ilb_admin_client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestEditUserImporterPermissionsView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse(
            "edit-user-importer-permissions",
            kwargs={"org_pk": self.importer.id, "user_pk": self.importer_user.id},
        )

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        #
        # Removing the manage permission should cause the importer user to be forbidden
        #
        remove_perm(
            Perms.obj.importer.manage_contacts_and_agents, self.importer_user, self.importer
        )
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["page_title"] == "Edit Importer user permissions"
        assert response.context["org_type"] == "Importer"
        assert response.context["contact"] == self.importer_user
        assert response.context["organisation"] == self.importer

    def test_post(self):
        data = {
            "permissions": [
                Perms.obj.importer.edit.codename,
                Perms.obj.importer.manage_contacts_and_agents.codename,
            ]
        }
        response = self.ilb_admin_client.post(self.url, data)

        assert response.status_code == HTTPStatus.FOUND

        self.importer_user.refresh_from_db()

        perms = self.importer_user.get_all_permissions(self.importer)
        assert perms == {
            Perms.obj.importer.edit.codename,
            Perms.obj.importer.manage_contacts_and_agents.codename,
        }
