import datetime as dt
from http import HTTPStatus
from unittest import mock

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects

from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.forms.fields import JQUERY_DATE_FORMAT
from web.mail.constants import EmailTypes
from web.mail.url_helpers import get_case_view_url, get_validate_digital_signatures_url
from web.models import (
    Constabulary,
    Country,
    ImportApplicationLicence,
    ImportApplicationType,
    OILSupplementaryReport,
    OILSupplementaryReportFirearm,
    OpenIndividualLicenceApplication,
    Task,
)
from web.sites import SiteName, get_importer_site_domain
from web.tests.application_utils import (
    add_app_file,
    compare_import_application_with_fixture,
    create_import_app,
    save_app_data,
    submit_app,
)
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.domains.case._import.factory import OILApplicationFactory
from web.tests.helpers import CaseURLS, check_gov_notify_email_was_sent


def test_create_in_progress_fa_oil_application(
    importer_client, importer, office, importer_one_contact, fa_oil_app_in_progress
):
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-oil",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )
    any_country = Country.objects.get(name="Any Country", is_active=True)

    form_data = {
        "contact": importer_one_contact.pk,
        "applicant_reference": "applicant_reference value",
        "section1": True,
        "section2": True,
        "origin_country": any_country.pk,
        "consignment_country": any_country.pk,
        "commodity_code": "ex Chapter 93",
        "know_bought_from": False,
    }
    save_app_data(
        client=importer_client, view_name="import:fa-oil:edit", app_pk=app_pk, form_data=form_data
    )

    post_data = {
        "reference": "Certificate Reference Value",
        "certificate_type": "registered",
        "constabulary": Constabulary.objects.first().pk,
        "date_issued": dt.date.today().strftime(JQUERY_DATE_FORMAT),
        "expiry_date": dt.date.today().strftime(JQUERY_DATE_FORMAT),
    }

    add_app_file(
        client=importer_client,
        view_name="import:fa:create-certificate",
        app_pk=app_pk,
        post_data=post_data,
    )

    # Set the know_bought_from value
    form_data = {"know_bought_from": False}
    importer_client.post(CaseURLS.fa_manage_import_contacts(app_pk), form_data)

    oil_app = OpenIndividualLicenceApplication.objects.get(pk=app_pk)
    case_progress.check_expected_status(oil_app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(oil_app, Task.TaskType.PREPARE)

    # Compare created application using views matches the test fixture
    compare_import_application_with_fixture(
        oil_app, fa_oil_app_in_progress, ["user_imported_certificates"]
    )

    # Compare files
    assert (
        oil_app.user_imported_certificates.count()
        == fa_oil_app_in_progress.user_imported_certificates.count()
    )


def test_submit_fa_oil_application(importer_client, fa_oil_app_in_progress, fa_oil_app_submitted):
    submit_app(
        client=importer_client,
        view_name="import:fa-oil:submit-oil",
        app_pk=fa_oil_app_in_progress.pk,
    )

    fa_oil_app_in_progress.refresh_from_db()

    case_progress.check_expected_status(fa_oil_app_in_progress, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(fa_oil_app_in_progress, Task.TaskType.PROCESS)

    # Compare created application using views matches the test fixture
    compare_import_application_with_fixture(
        fa_oil_app_in_progress, fa_oil_app_submitted, ["user_imported_certificates", "reference"]
    )

    # Compare files
    assert (
        fa_oil_app_in_progress.user_imported_certificates.count()
        == fa_oil_app_submitted.user_imported_certificates.count()
    )

    # Check both the submitted app and the fixture have a linked supplementary_info record.
    assert fa_oil_app_in_progress.supplementary_info
    assert fa_oil_app_submitted.supplementary_info


def test_submit_fa_oil_application_without_certificates(fa_oil_app_in_progress, importer_client):
    app = fa_oil_app_in_progress

    app.user_imported_certificates.all().delete()
    submit_url = CaseURLS.fa_oil_submit(app.pk)
    response = importer_client.get(submit_url)
    assert response.status_code == HTTPStatus.OK

    form_data = {"confirmation": "I AGREE"}
    response = importer_client.post(submit_url, form_data)
    assert response.status_code == HTTPStatus.OK
    certificate_errors = response.context["errors"].get_page_errors("Certificates").errors
    assert len(response.context["errors"].page_errors) == 4  # Not sure why this is 4
    assert len(certificate_errors) == 1
    assert certificate_errors[0].messages[0] == "At least one certificate must be added"
    assert certificate_errors[0].field_name == "Certificate"


def test_submit_fa_oil_application_without_contacts(fa_oil_app_in_progress, importer_client):
    app = fa_oil_app_in_progress

    app.importcontact_set.all().delete()
    app.know_bought_from = True
    app.save()
    submit_url = CaseURLS.fa_oil_submit(app.pk)
    response = importer_client.get(submit_url)
    assert response.status_code == HTTPStatus.OK

    form_data = {"confirmation": "I AGREE"}
    response = importer_client.post(submit_url, form_data)
    assert response.status_code == HTTPStatus.OK
    field_errors = response.context["errors"].get_page_errors("Details of who bought from").errors
    assert len(response.context["errors"].page_errors) == 4  # Not sure why this is 4
    assert len(field_errors) == 1
    assert field_errors[0].messages[0] == "At least one person must be added"
    assert field_errors[0].field_name == "Person"


class TestImportApplicationCreateView(AuthTestCase):
    url = reverse("import:create-fa-oil")
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_create_ok(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.post(
            reverse("import:create-fa-oil"),
            data={"importer": self.importer.pk, "importer_office": self.importer_office.pk},
        )
        assert response.status_code == HTTPStatus.FOUND

        application = OpenIndividualLicenceApplication.objects.get(importer_id=self.importer.pk)
        assert application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE

        application_type = application.application_type
        assert application_type.type == ImportApplicationType.Types.FIREARMS
        assert application_type.sub_type == ImportApplicationType.SubTypes.OIL

        task = application.tasks.get()
        assert task.task_type == Task.TaskType.PREPARE
        assert task.is_active is True

    def test_create_missing_office(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.post(
            reverse("import:create-fa-oil"), data={"importer": self.importer.pk}
        )
        assert response.status_code == HTTPStatus.OK
        assertInHTML(
            '<div class="error-message">You must enter this item', response.content.decode("utf-8")
        )

    def test_anonymous_post_access_redirects(self):
        response = self.anonymous_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

    def test_forbidden_post_access(self):
        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_take_ownership(importer_one_contact, importer, ilb_admin_client):
    process = OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
    )
    Task.objects.create(process=process, task_type=Task.TaskType.PROCESS)
    oil_app = process.get_specific_model()
    oil_app.licences.create()

    response_workbasket = ilb_admin_client.get("/workbasket/")
    assert "Take Ownership" in response_workbasket.content.decode()

    # After taking ownership we now navigate to the case management "view application" view.
    response = ilb_admin_client.post(
        f"/case/import/{process.pk}/admin/take-ownership/", follow=True
    )

    assert response.status_code == HTTPStatus.OK
    view_application_response = response.content.decode()
    assert "Firearms and Ammunition (Open Individual Import Licence)" in view_application_response


@pytest.mark.django_db
def test_release_ownership(ilb_admin_user, ilb_admin_client, importer, importer_one_contact):
    process = OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        case_owner=ilb_admin_user,
    )
    Task.objects.create(process=process, task_type=Task.TaskType.PROCESS)

    response = ilb_admin_client.post(
        f"/case/import/{process.pk}/admin/release-ownership/", follow=True
    )

    assert "Manage" in response.content.decode()


@pytest.mark.django_db
def test_close_case(ilb_admin_user, ilb_admin_client, importer, importer_one_contact):
    process = OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        case_owner=ilb_admin_user,
        reference="IMA/123/4567",
    )
    task = Task.objects.create(process=process, task_type=Task.TaskType.PROCESS)
    licence = document_pack.pack_draft_create(process)

    ilb_admin_client.post(
        f"/case/import/{process.pk}/admin/manage/", data={"send_email": True}, follow=True
    )

    process.refresh_from_db()
    assert process.status == "STOPPED"

    licence.refresh_from_db()
    assert licence.status == document_pack.PackStatus.ARCHIVED

    task.refresh_from_db()
    assert task.is_active is False
    check_gov_notify_email_was_sent(
        1,
        ["I1_main_contact@example.com"],  # /PS-IGNORE
        EmailTypes.APPLICATION_STOPPED,
        {
            "reference": process.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(
                get_importer_site_domain()
            ),
            "application_url": get_case_view_url(process, get_importer_site_domain()),
            "icms_url": get_importer_site_domain(),
            "service_name": SiteName.IMPORTER.label,
        },
    )


def test_fa_oil_app_submitted_has_a_licence(fa_oil_app_submitted):
    assert fa_oil_app_submitted.licences.filter(
        status=ImportApplicationLicence.Status.DRAFT
    ).exists()


def test_manage_checklist(fa_oil_app_submitted, ilb_admin_client):
    app = fa_oil_app_submitted

    assert not hasattr(app, "checklist")

    manage_checklist = CaseURLS.fa_oil_manage_checklist(app.pk)
    resp = ilb_admin_client.get(manage_checklist)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["page_title"] == "Open Individual Import Licence - Checklist"
    assert resp.context["readonly_view"] is True

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
    resp = ilb_admin_client.get(manage_checklist)
    assert resp.context["readonly_view"] is False

    app.refresh_from_db()
    assert hasattr(app, "checklist")

    post_data = {
        "case_update": "yes",
        "fir_required": "yes",
        "response_preparation": True,
        "validity_period_correct": "yes",
        "endorsements_listed": "yes",
        "authorisation": True,
        "authority_required": "yes",
        "authority_received": "yes",
        "authority_police": "yes",
    }
    resp = ilb_admin_client.post(manage_checklist, data=post_data, follow=True)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {}


def test_manage_checklist_errors(fa_oil_app_submitted, ilb_admin_client):
    app = fa_oil_app_submitted
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
    manage_checklist = CaseURLS.fa_oil_manage_checklist(app.pk)
    resp = ilb_admin_client.post(manage_checklist, data={}, follow=True)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {
        "authorisation": ["You must enter this item"],
        "authority_police": ["You must enter this item"],
        "authority_received": ["You must enter this item"],
        "authority_required": ["You must enter this item"],
        "case_update": ["You must enter this item"],
        "endorsements_listed": ["You must enter this item"],
        "fir_required": ["You must enter this item"],
        "response_preparation": ["You must enter this item"],
        "validity_period_correct": ["You must enter this item"],
    }


def test_fa_oil_delete_report(completed_oil_app_with_supplementary_report, importer_client):
    app = completed_oil_app_with_supplementary_report
    report: OILSupplementaryReport = app.supplementary_info.reports.first()
    report_firearm: OILSupplementaryReportFirearm = report.firearms.first()

    assert OILSupplementaryReport.objects.filter(pk=report.pk).exists() is True
    assert OILSupplementaryReportFirearm.objects.filter(pk=report_firearm.pk).exists() is True

    url = CaseURLS.fa_oil_report_manual_delete(app.pk, report.pk, report_firearm.pk)
    resp = importer_client.post(url, data={})
    assert resp.status_code == HTTPStatus.FOUND

    assert OILSupplementaryReport.objects.filter(pk=report.pk).exists() is True
    assert OILSupplementaryReportFirearm.objects.filter(pk=report_firearm.pk).exists() is False


@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_fa_oil_view_upload_document(
    mock_get_file_from_s3, completed_oil_app_with_supplementary_report, importer_client
):
    mock_get_file_from_s3.return_value = b"test_file"
    app = completed_oil_app_with_supplementary_report
    report: OILSupplementaryReport = app.supplementary_info.reports.first()
    report_firearm: OILSupplementaryReportFirearm = report.firearms.first()

    url = CaseURLS.fa_oil_report_upload_view(app.pk, report.pk, report_firearm.pk)
    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert mock_get_file_from_s3.called is True


def test_fa_oil_report_firearm_manual_add(
    completed_oil_app_with_supplementary_report, importer_client
):
    app = completed_oil_app_with_supplementary_report
    report: OILSupplementaryReport = app.supplementary_info.reports.first()
    report.firearms.all().delete()
    report.refresh_from_db()
    assert report.firearms.count() == 0

    url = CaseURLS.fa_oil_report_manual_add(app.pk, report.pk)

    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["page_title"] == "Add Firearm Details"

    resp = importer_client.post(url, data={})
    assert resp.status_code == HTTPStatus.OK

    assert resp.context["form"].errors == {
        "calibre": ["You must enter this item"],
        "model": ["You must enter this item"],
        "proofing": ["You must enter this item"],
        "serial_number": ["You must enter this item"],
    }

    assert report.firearms.count() == 0

    resp = importer_client.post(
        url, data={"calibre": "7", "model": "GP", "proofing": "yes", "serial_number": "7"}
    )
    assert resp.status_code == HTTPStatus.FOUND
    assert report.firearms.count() == 1


def test_fa_oil_report_firearm_manual_edit(
    completed_oil_app_with_supplementary_report, importer_client
):
    app = completed_oil_app_with_supplementary_report
    report: OILSupplementaryReport = app.supplementary_info.reports.first()
    report_firearm: OILSupplementaryReportFirearm = report.firearms.first()

    url = CaseURLS.fa_oil_report_manual_edit(app.pk, report.pk, report_firearm.pk)
    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["page_title"] == "Edit Firearm Details"

    resp = importer_client.post(
        url, data={"calibre": "7", "model": "GP", "proofing": "yes", "serial_number": "7"}
    )
    assert resp.status_code == HTTPStatus.FOUND

    report_firearm.refresh_from_db()
    assert report_firearm.calibre == "7"
    assert report_firearm.model == "GP"
    assert report_firearm.proofing == "yes"
    assert report_firearm.serial_number == "7"


def test_fa_oil_report_firearm_manual_edit_permission_denied(
    completed_oil_app_with_supplementary_report, importer_two_client
):
    app = completed_oil_app_with_supplementary_report
    report: OILSupplementaryReport = app.supplementary_info.reports.first()
    report_firearm: OILSupplementaryReportFirearm = report.firearms.first()

    url = CaseURLS.fa_oil_report_manual_edit(app.pk, report.pk, report_firearm.pk)
    resp = importer_two_client.get(url)
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_fa_oil_report_firearm_upload(completed_oil_app_with_supplementary_report, importer_client):
    app = completed_oil_app_with_supplementary_report
    report: OILSupplementaryReport = app.supplementary_info.reports.first()

    url = CaseURLS.fa_oil_report_upload_add(app.pk, report.pk)
    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["page_title"] == "Add Firearm Details"

    resp = importer_client.post(url, data={})
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {"file": ["You must enter this item"]}
