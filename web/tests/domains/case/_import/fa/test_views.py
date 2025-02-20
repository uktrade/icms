from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertFormError, assertRedirects, assertTemplateUsed

from web.domains.case.shared import ImpExpStatus
from web.models import (
    Country,
    DFLApplication,
    DFLSupplementaryInfo,
    ImportApplicationType,
    ImportContact,
    Task,
)
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS


@pytest.fixture()
def dfl_app(importer_one_contact, importer, office):
    app = DFLApplication.objects.create(
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
        ),
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        importer=importer,
        importer_office=office,
        status=ImpExpStatus.IN_PROGRESS,
        know_bought_from=False,
    )

    app.tasks.create(task_type=Task.TaskType.PREPARE)

    app.importcontact_set.create(
        entity=ImportContact.LEGAL,
        first_name="Foo",
        last_name="Bar",
        street="Some street",
        city="Some city",
        postcode="Some postcode",
        country=Country.objects.first(),
        dealer="yes",
    )

    return app


class TestManageImportContactsView:
    @pytest.fixture(autouse=True)
    def setup(self, dfl_app):
        self.app = dfl_app
        self.url = CaseURLS.fa_manage_import_contacts(self.app.pk)

    def test_permission(self, ilb_admin_client, importer_client, exporter_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post_successful(self, importer_client):
        assert self.app.know_bought_from is False

        response = importer_client.post(self.url, data={"know_bought_from": True})

        assertRedirects(
            response,
            self.url,
            HTTPStatus.FOUND,
        )
        self.app.refresh_from_db()
        assert self.app.know_bought_from is True

    @pytest.mark.parametrize(
        "know_bought_from,exp_msg",
        (
            (
                False,
                "You will be asked to provide this information after the import licence has been issued. An export authority cannot issue a "
                "firearms export licence until this information has been provided",
            ),
            (
                True,
                "You must provide details of who you plan to buy/obtain these items from using one of the Add Who Bought From buttons below.",
            ),
        ),
    )
    def test_messaging(self, importer_client, know_bought_from, exp_msg):
        self.app.importcontact_set.all().delete()
        response = importer_client.post(
            self.url, data={"know_bought_from": know_bought_from}, follow=True
        )
        assert exp_msg in response.content.decode("utf-8")
        self.app.refresh_from_db()
        assert self.app.know_bought_from is know_bought_from

    def test_form_errors(self, importer_client):
        # Test field is required
        response = importer_client.post(self.url, data={"know_bought_from": ""})
        assertFormError(response.context["form"], "know_bought_from", "This field is required.")

        # Test setting to false errors when there are import contacts.
        self.app.know_bought_from = True
        self.app.save()
        response = importer_client.post(self.url, data={"know_bought_from": False})
        assertFormError(
            response.context["form"],
            "know_bought_from",
            "Please remove contacts before setting this to No.",
        )


class TestCreateImportContactView:
    @pytest.fixture(autouse=True)
    def setup(self, dfl_app):
        self.app = dfl_app
        self.url = CaseURLS.fa_create_import_contact(self.app.pk, ImportContact.LEGAL)

    def test_permission(self, ilb_admin_client, importer_client, exporter_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_correct_template_used(self, importer_client):
        response = importer_client.get(self.url)
        assertTemplateUsed(response, "web/domains/case/import/fa/import-contacts/create.html")

        # Now check the complete app
        self.app.status = ImpExpStatus.COMPLETED
        self.app.save()

        response = importer_client.get(self.url)
        assertTemplateUsed(
            response, "web/domains/case/import/fa/provide-report/import-contacts.html"
        )

    def test_in_progress_application_post_success(self, importer_client):
        response = importer_client.post(
            self.url,
            data={
                "first_name": "first_name value",
                "registration_number": "registration_number value",
                "street": "street value",
                "city": "city value",
                "postcode": "postcode value",
                "region": "region value",
                "country": Country.objects.first().pk,
                "dealer": "yes",
            },
        )

        assertRedirects(
            response,
            CaseURLS.fa_manage_import_contacts(self.app.pk),
            HTTPStatus.FOUND,
        )

        self.app.refresh_from_db()
        assert self.app.importcontact_set.filter(first_name="first_name value").exists()

    def test_complete_application_post_success(self, importer_client):
        self.app.status = ImpExpStatus.COMPLETED
        self.app.save()

        DFLSupplementaryInfo.objects.create(import_application=self.app.get_specific_model())

        response = importer_client.post(
            self.url,
            data={
                "first_name": "first_name value",
                "registration_number": "registration_number value",
                "street": "street value",
                "city": "city value",
                "postcode": "postcode value",
                "region": "region value",
                "country": Country.objects.first().pk,
                "dealer": "yes",
            },
        )

        assertRedirects(
            response,
            reverse("import:fa:provide-report", kwargs={"application_pk": self.app.pk}),
            HTTPStatus.FOUND,
        )

        self.app.refresh_from_db()
        assert self.app.importcontact_set.filter(first_name="first_name value").exists()


class TestEditImportContactView:
    @pytest.fixture(autouse=True)
    def setup(self, dfl_app):
        self.app = dfl_app
        self.contact = self.app.importcontact_set.first()

        self.url = reverse(
            "import:fa:edit-import-contact",
            kwargs={
                "application_pk": self.app.pk,
                "entity": ImportContact.LEGAL,
                "contact_pk": self.contact.pk,
            },
        )

    def test_permission(self, ilb_admin_client, importer_client, exporter_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_correct_template_used(self, importer_client):
        response = importer_client.get(self.url)
        assertTemplateUsed(response, "web/domains/case/import/fa/import-contacts/edit.html")

        # Now check the complete app
        self.app.status = ImpExpStatus.COMPLETED
        self.app.save()

        response = importer_client.get(self.url)
        assertTemplateUsed(
            response, "web/domains/case/import/fa/provide-report/import-contacts.html"
        )

    def test_in_progress_application_post_success(self, importer_client):
        response = importer_client.post(
            self.url,
            data={
                "first_name": "first_name new value",
                "street": self.contact.street,
                "city": self.contact.city,
                "country": self.contact.country.pk,
                "dealer": self.contact.dealer,
            },
        )

        assertRedirects(
            response,
            CaseURLS.fa_manage_import_contacts(self.app.pk),
            HTTPStatus.FOUND,
        )

        self.app.refresh_from_db()
        assert self.app.importcontact_set.filter(first_name="first_name new value").exists()

    def test_complete_application_post_success(self, importer_client):
        self.app.status = ImpExpStatus.COMPLETED
        self.app.save()

        DFLSupplementaryInfo.objects.create(import_application=self.app.get_specific_model())

        response = importer_client.post(
            self.url,
            data={
                "first_name": "first_name new value",
                "street": self.contact.street,
                "city": self.contact.city,
                "country": self.contact.country.pk,
                "dealer": self.contact.dealer,
            },
        )

        assertRedirects(
            response,
            reverse("import:fa:provide-report", kwargs={"application_pk": self.app.pk}),
            HTTPStatus.FOUND,
        )

        self.app.refresh_from_db()
        assert self.app.importcontact_set.filter(first_name="first_name new value").exists()


class TestDeleteImportContactView:
    @pytest.fixture(autouse=True)
    def setup(self, dfl_app):
        self.app = dfl_app
        contact = self.app.importcontact_set.first()

        self.url = reverse(
            "import:fa:delete-import-contact",
            kwargs={
                "application_pk": self.app.pk,
                "entity": ImportContact.LEGAL,
                "contact_pk": contact.pk,
            },
        )

    def test_post_only(self, importer_client):
        response = importer_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_exporter_forbidden(self, exporter_client):
        response = exporter_client.post(self.url)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_in_progress_application_post_success(self, importer_client):
        response = importer_client.post(self.url)

        assertRedirects(
            response,
            reverse("import:fa:manage-import-contacts", kwargs={"application_pk": self.app.pk}),
            status_code=HTTPStatus.FOUND,
        )

    def test_complete_application_post_success(self, importer_client):
        self.app.status = ImpExpStatus.COMPLETED
        self.app.save()
        DFLSupplementaryInfo.objects.create(import_application=self.app.get_specific_model())

        response = importer_client.post(self.url)

        assertRedirects(
            response,
            reverse("import:fa:provide-report", kwargs={"application_pk": self.app.pk}),
            status_code=HTTPStatus.FOUND,
        )


def test_upload_supplementary_report_search_redirect(
    completed_oil_app_with_supplementary_report, importer_client
):
    """Tests that accessing the upload supplementary report page redirects to the search results page when the user
    has accessed it from there."""
    # Add Report
    response = importer_client.post(
        CaseURLS.fa_provide_report(completed_oil_app_with_supplementary_report.pk),
        follow=True,
        headers={"REFERER": "https://example.com/case/import/search/standard/?test=yes"},
    )

    assert response.resolver_match.view_name == "case:search-results"
    assert response.resolver_match.kwargs["mode"] == "standard"
    assert response.resolver_match.kwargs["case_type"] == "import"
    assert response.request["QUERY_STRING"] == "test=yes"


class TestViewFirearmsReportDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, completed_oil_app_with_supplementary_report):
        self.app = completed_oil_app_with_supplementary_report
        self.url = CaseURLS.fa_view_report(self.app.pk)

    def test_permission(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        context = response.context
        assert context["ilb_read_only"]
        assert context["process"] == self.app

        html = response.content.decode("utf-8")
        assert "Reopen" not in html
        assert '<button type="submit"' not in html

    def test_post_forbidden(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
