from http import HTTPStatus
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from pytest_django.asserts import (
    assertContains,
    assertFormError,
    assertRedirects,
    assertTemplateUsed,
)

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.models import (
    Constabulary,
    Country,
    DFLApplication,
    DFLGoodsCertificate,
    ImportApplicationLicence,
    Task,
    User,
)
from web.models.shared import FirearmCommodity
from web.tests.application_utils import (
    add_app_file,
    compare_import_application_with_fixture,
    create_import_app,
    save_app_data,
    submit_app,
)
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS, check_page_errors, get_test_client


def test_create_in_progress_fa_dfl_application(
    importer_client, importer, office, importer_one_contact, fa_dfl_app_in_progress
):
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-dfl",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )

    # Save a valid set of data.
    dfl_countries = Country.util.get_all_countries()
    origin_country = dfl_countries[0]
    consignment_country = dfl_countries[1]
    constabulary = Constabulary.objects.get(name="Derbyshire")
    form_data = {
        "contact": importer_one_contact.pk,
        "applicant_reference": "applicant_reference value",
        "deactivated_firearm": True,
        "proof_checked": True,
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "commodity_code": FirearmCommodity.EX_CHAPTER_93.value,
        "constabulary": constabulary.pk,
    }
    save_app_data(
        client=importer_client, view_name="import:fa-dfl:edit", app_pk=app_pk, form_data=form_data
    )
    issuing_country = Country.app.get_fa_dfl_issuing_countries().first()

    # Add a goods file to the fa-dfl app
    post_data = {
        "goods_description": "goods_description value",
        "deactivated_certificate_reference": "deactivated_certificate_reference value",
        "issuing_country": issuing_country.pk,
    }
    add_app_file(
        client=importer_client,
        view_name="import:fa-dfl:add-goods",
        app_pk=app_pk,
        post_data=post_data,
    )

    # Set the know_bought_from value
    form_data = {"know_bought_from": False}
    importer_client.post(CaseURLS.fa_manage_import_contacts(app_pk), form_data)

    dfl_app = DFLApplication.objects.get(pk=app_pk)

    case_progress.check_expected_status(dfl_app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(dfl_app, Task.TaskType.PREPARE)

    # Compare created application using views matches the test fixture
    compare_import_application_with_fixture(dfl_app, fa_dfl_app_in_progress, ["goods_certificates"])

    # Compare files
    assert dfl_app.goods_certificates.count() == fa_dfl_app_in_progress.goods_certificates.count()


def test_submit_fa_dfl_application(importer_client, fa_dfl_app_in_progress, fa_dfl_app_submitted):
    submit_app(
        client=importer_client, view_name="import:fa-dfl:submit", app_pk=fa_dfl_app_in_progress.pk
    )

    fa_dfl_app_in_progress.refresh_from_db()

    case_progress.check_expected_status(fa_dfl_app_in_progress, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(fa_dfl_app_in_progress, Task.TaskType.PROCESS)

    # Compare created application using views matches the test fixture
    compare_import_application_with_fixture(
        fa_dfl_app_in_progress, fa_dfl_app_in_progress, ["goods_certificates", "reference"]
    )

    # Compare files
    assert (
        fa_dfl_app_in_progress.goods_certificates.count()
        == fa_dfl_app_submitted.goods_certificates.count()
    )

    # Check both the submitted app and the fixture have a linked supplementary_info record.
    assert fa_dfl_app_in_progress.supplementary_info
    assert fa_dfl_app_submitted.supplementary_info


def test_edit_dfl_get(
    fa_dfl_app_in_progress, importer_client, exporter_client, importer_two_contact, importer_site
):
    dfl_app_pk = fa_dfl_app_in_progress.pk
    url = CaseURLS.fa_dfl_edit(dfl_app_pk)

    response = importer_client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Edit",
        status_code=HTTPStatus.OK,
    )

    # Check permissions
    # Exporter can't access it
    response = exporter_client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN

    # A different importer can't access it
    importer_two_client = get_test_client(importer_site.domain, importer_two_contact)
    response = importer_two_client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_validate_query_param_shows_errors(importer_client, importer, office):
    dfl_app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-dfl",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )
    url = CaseURLS.fa_dfl_edit(dfl_app_pk)

    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    form = response.context["form"]
    assert not form.errors

    response = importer_client.get(f"{url}?validate")
    assert response.status_code == HTTPStatus.OK

    assertFormError(response.context["form"], "proof_checked", "You must enter this item")
    assertFormError(response.context["form"], "origin_country", "You must enter this item")
    assertFormError(response.context["form"], "consignment_country", "You must enter this item")
    assertFormError(response.context["form"], "contact", "You must enter this item")
    assertFormError(response.context["form"], "constabulary", "You must enter this item")


def test_edit_dfl_post_valid(fa_dfl_app_in_progress, importer_client, importer_one_contact):
    dfl_app_pk = fa_dfl_app_in_progress.pk
    url = CaseURLS.fa_dfl_edit(dfl_app_pk)

    dfl_countries = Country.util.get_all_countries()
    origin_country = dfl_countries[0]
    consignment_country = dfl_countries[1]
    constabulary = Constabulary.objects.first()

    form_data = {
        "applicant_reference": "applicant_reference value",
        "deactivated_firearm": True,
        "proof_checked": True,
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "contact": importer_one_contact.pk,
        "commodity_code": FirearmCommodity.EX_CHAPTER_93.value,
        "constabulary": constabulary.pk,
    }
    response = importer_client.post(url, form_data)

    assertRedirects(response, url, HTTPStatus.FOUND)

    # check the data has been saved:
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)
    assert dfl_app.applicant_reference == "applicant_reference value"
    assert dfl_app.deactivated_firearm is True
    assert dfl_app.proof_checked is True
    assert dfl_app.origin_country.pk == origin_country.pk
    assert dfl_app.consignment_country.pk == consignment_country.pk
    assert dfl_app.contact.pk == importer_one_contact.pk
    assert dfl_app.commodity_code == FirearmCommodity.EX_CHAPTER_93.value
    assert dfl_app.constabulary.pk == constabulary.pk


def test_add_goods_document_get(fa_dfl_app_in_progress, importer_client):
    dfl_app_pk = fa_dfl_app_in_progress.pk
    url = CaseURLS.fa_dfl_add_goods(dfl_app_pk)
    response = importer_client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Add Goods Certificate",
        status_code=HTTPStatus.OK,
    )


def test_add_goods_document_post_invalid(fa_dfl_app_in_progress, importer_client):
    dfl_app_pk = fa_dfl_app_in_progress.pk
    url = CaseURLS.fa_dfl_add_goods(dfl_app_pk)
    form_data = {"foo": "bar"}
    response = importer_client.post(url, form_data)

    assertFormError(response.context["form"], "goods_description", "You must enter this item")
    assertFormError(
        response.context["form"], "deactivated_certificate_reference", "You must enter this item"
    )
    assertFormError(response.context["form"], "issuing_country", "You must enter this item")
    assertFormError(response.context["form"], "document", "You must enter this item")


def test_add_goods_document_post_valid(fa_dfl_app_in_progress, importer_client):
    dfl_app_pk = fa_dfl_app_in_progress.pk
    url = CaseURLS.fa_dfl_add_goods(dfl_app_pk)
    issuing_country = Country.app.get_fa_dfl_issuing_countries().first()
    goods_file = SimpleUploadedFile("myimage.png", b"file_content")

    form_data = {
        "goods_description": "goods_description value",
        "deactivated_certificate_reference": "deactivated_certificate_reference value",
        "issuing_country": issuing_country.pk,
        "document": goods_file,
    }

    response = importer_client.post(url, form_data)

    assertRedirects(response, CaseURLS.fa_dfl_list_goods(dfl_app_pk), HTTPStatus.FOUND)

    # Check the record has a file
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)

    assert dfl_app.goods_certificates.count() == 2

    goods_cert = dfl_app.goods_certificates.first()
    assert goods_cert.goods_description == "goods_description value"
    assert goods_cert.deactivated_certificate_reference == "deactivated_certificate_reference value"
    assert goods_cert.issuing_country.pk == issuing_country.pk
    assert goods_cert.is_active is True
    assert goods_cert.path == "myimage.png"
    assert goods_cert.filename == "original_name: myimage.png"
    assert goods_cert.content_type == "text/plain"
    assert goods_cert.file_size == goods_file.size


def test_edit_goods_certificate_get(fa_dfl_app_in_progress, importer_client):
    dfl_app_pk = fa_dfl_app_in_progress.pk
    document_pk = _create_goods_cert(dfl_app_pk)
    url = CaseURLS.fa_dfl_edit_goods(dfl_app_pk, document_pk)
    response = importer_client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Edit Goods Certificate",
        status_code=HTTPStatus.OK,
    )


def test_edit_goods_certificate_post_invalid(fa_dfl_app_in_progress, importer_client):
    dfl_app_pk = fa_dfl_app_in_progress.pk
    document_pk = _create_goods_cert(dfl_app_pk)
    url = CaseURLS.fa_dfl_edit_goods(dfl_app_pk, document_pk)
    form_data = {
        "goods_description": "",
        "deactivated_certificate_reference": "",
        "issuing_country": -1,
    }
    response = importer_client.post(url, form_data)

    assertFormError(
        response.context["form"], "deactivated_certificate_reference", "You must enter this item"
    )
    assertFormError(
        response.context["form"],
        "issuing_country",
        "Select a valid choice. That choice is not one of the available choices.",
    )
    assertFormError(response.context["form"], "goods_description", "You must enter this item")


def test_edit_goods_certificate_post_valid(fa_dfl_app_in_progress, importer_client):
    dfl_app_pk = fa_dfl_app_in_progress.pk
    document_pk = _create_goods_cert(dfl_app_pk)
    url = CaseURLS.fa_dfl_edit_goods(dfl_app_pk, document_pk)

    issuing_country = Country.app.get_fa_dfl_issuing_countries().first()
    form_data = {
        "goods_description": "New goods description",
        "deactivated_certificate_reference": "New deactived certificate reference",
        "issuing_country": issuing_country.pk,
    }
    response = importer_client.post(url, form_data)

    assertRedirects(response, CaseURLS.fa_dfl_list_goods(dfl_app_pk), HTTPStatus.FOUND)

    # Check the record has a file
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)

    assert dfl_app.goods_certificates.count() == 2

    goods_cert = dfl_app.goods_certificates.first()
    assert goods_cert.goods_description == "New goods description"
    assert goods_cert.deactivated_certificate_reference == "New deactived certificate reference"
    assert goods_cert.issuing_country.pk == issuing_country.pk


def _create_goods_cert(dfl_app_pk):
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)
    issuing_country = Country.app.get_fa_dfl_issuing_countries().first()
    dfl_app.goods_certificates.create(
        filename="test-file.txt",
        goods_description="goods_description value",
        deactivated_certificate_reference="deactivated_certificate_reference value",
        issuing_country=issuing_country,
        file_size=1024,
        created_by=User.objects.get(username="I1_main_contact"),
    )
    document_pk = dfl_app.goods_certificates.first().pk

    return document_pk


def test_submit_dfl_get(importer_client, importer, office):
    dfl_app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-dfl",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )
    url = CaseURLS.fa_dfl_submit(dfl_app_pk)

    response = importer_client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Submit Application",
        status_code=HTTPStatus.OK,
    )

    assertTemplateUsed(response, "web/domains/case/import/import-case-submit.html")

    # check the errors are displayed in the response
    errors = response.context["errors"]

    check_page_errors(
        errors,
        "Application Details",
        [
            "Proof Checked",
            "Country Of Origin",
            "Country Of Consignment",
            "Contact",
            "Constabulary",
        ],
    )

    check_page_errors(errors, "Application Details - Goods Certificates", ["Goods Certificate"])

    check_page_errors(
        errors,
        "Application Details - Details of Who Bought From",
        ["Do you know who you plan to buy/obtain these items from?"],
    )


def test_submit_dfl_post_invalid(importer_client, importer_one_contact, importer, office):
    dfl_app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-dfl",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )
    submit_url = CaseURLS.fa_dfl_submit(dfl_app_pk)

    form_data = {"foo": "bar"}

    response = importer_client.post(submit_url, form_data)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Submit Application",
        status_code=HTTPStatus.OK,
    )

    errors = response.context["errors"]

    check_page_errors(
        errors,
        "Application Details",
        [
            "Proof Checked",
            "Country Of Origin",
            "Country Of Consignment",
            "Contact",
            "Constabulary",
        ],
    )

    check_page_errors(errors, "Application Details - Goods Certificates", ["Goods Certificate"])

    check_page_errors(
        errors,
        "Application Details - Details of Who Bought From",
        ["Do you know who you plan to buy/obtain these items from?"],
    )

    assertFormError(response.context["form"], "confirmation", "You must enter this item")

    form_data = {"confirmation": "I will NEVER agree"}
    response = importer_client.post(submit_url, form_data)

    assertFormError(
        response.context["form"], "confirmation", "Please agree to the declaration of truth."
    )

    # Test the know bought from check
    dfl_countries = Country.util.get_all_countries()
    origin_country = dfl_countries[0]
    consignment_country = dfl_countries[1]
    constabulary = Constabulary.objects.first()

    form_data = {
        "applicant_reference": "applicant_reference value",
        "deactivated_firearm": True,
        "proof_checked": True,
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "contact": importer_one_contact.pk,
        "commodity_code": FirearmCommodity.EX_CHAPTER_93.value,
        "constabulary": constabulary.pk,
    }
    edit_url = CaseURLS.fa_dfl_edit(dfl_app_pk)
    importer_client.post(edit_url, form_data)

    # Save the know bought from to make the application valid.
    form_data = {"know_bought_from": True}
    importer_client.post(
        CaseURLS.fa_manage_import_contacts(dfl_app_pk),
        form_data,
    )

    # now we have a valid application submit the application again to see the know_bought_from error
    response = importer_client.post(submit_url, form_data)
    errors = response.context["errors"]
    check_page_errors(errors, "Application Details - Details of Who Bought From", ["Person"])


def test_submit_dfl_post_valid(fa_dfl_app_in_progress, importer_client, importer_one_contact):
    """Test the full happy path.

    Create the main application
    create a document
    Save the know bought from value
    submit the application
    """
    dfl_app_pk = fa_dfl_app_in_progress.pk
    edit_url = CaseURLS.fa_dfl_edit(dfl_app_pk)
    add_goods_url = CaseURLS.fa_dfl_add_goods(dfl_app_pk)
    know_bought_from_url = CaseURLS.fa_manage_import_contacts(dfl_app_pk)
    submit_url = CaseURLS.fa_dfl_submit(dfl_app_pk)

    dfl_countries = Country.util.get_all_countries()
    origin_country = dfl_countries[0]
    consignment_country = dfl_countries[1]
    constabulary = Constabulary.objects.first()

    form_data = {
        "applicant_reference": "applicant_reference value",
        "deactivated_firearm": True,
        "proof_checked": True,
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "contact": importer_one_contact.pk,
        "commodity_code": FirearmCommodity.EX_CHAPTER_93.value,
        "constabulary": constabulary.pk,
        "know_bought_from": False,
    }

    # Save the main application
    importer_client.post(edit_url, form_data)

    issuing_country = Country.app.get_fa_dfl_issuing_countries().first()
    goods_file = SimpleUploadedFile("myimage.png", b"file_content")

    form_data = {
        "goods_description": "goods_description value",
        "deactivated_certificate_reference": "deactivated_certificate_reference value",
        "issuing_country": issuing_country.pk,
        "document": goods_file,
    }

    # Save the goods certificate
    importer_client.post(add_goods_url, form_data)

    # Save the know bought from
    form_data = {"know_bought_from": False}
    importer_client.post(know_bought_from_url, form_data)

    form_data = {"confirmation": "I AGREE"}
    response = importer_client.post(submit_url, form_data)

    assertRedirects(response, reverse("workbasket"), HTTPStatus.FOUND)

    # check the application is in the correct state
    application = DFLApplication.objects.get(pk=dfl_app_pk)

    case_progress.check_expected_status(application, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(application, Task.TaskType.PROCESS)

    # And it has a draft licence
    assert application.licences.filter(status=ImportApplicationLicence.Status.DRAFT).exists()


def test_manage_checklist_errors(fa_dfl_app_submitted, ilb_admin_client):
    app = fa_dfl_app_submitted
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
    manage_checklist = CaseURLS.fa_dfl_manage_checklist(app.pk)
    resp = ilb_admin_client.post(manage_checklist, follow=True)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {
        "authorisation": ["You must enter this item"],
        "case_update": ["You must enter this item"],
        "endorsements_listed": ["You must enter this item"],
        "fir_required": ["You must enter this item"],
        "response_preparation": ["You must enter this item"],
        "validity_period_correct": ["You must enter this item"],
        "deactivation_certificate_attached": ["You must enter this item"],
        "deactivation_certificate_issued": ["You must enter this item"],
    }


def test_manage_checklist(fa_dfl_app_submitted, ilb_admin_client):
    app = fa_dfl_app_submitted

    assert not hasattr(app, "checklist")

    manage_checklist = CaseURLS.fa_dfl_manage_checklist(app.pk)
    resp = ilb_admin_client.get(manage_checklist)
    assert resp.status_code == HTTPStatus.OK
    assert (
        resp.context["page_title"]
        == "Firearms and Ammunition (Deactivated Firearms Licence) - Checklist"
    )
    assert resp.context["readonly_view"] is True

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
    resp = ilb_admin_client.get(manage_checklist)
    assert resp.context["readonly_view"] is False

    app.refresh_from_db()
    assert hasattr(app, "checklist")

    post_data = {
        "authorisation": "yes",
        "case_update": "yes",
        "endorsements_listed": "yes",
        "fir_required": "no",
        "response_preparation": "yes",
        "validity_period_correct": "no",
        "deactivation_certificate_attached": "yes",
        "deactivation_certificate_issued": "no",
    }
    resp = ilb_admin_client.post(manage_checklist, data=post_data, follow=True)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {}


def test_edit_goods_certificate_description(fa_dfl_app_submitted, ilb_admin_client):
    app = fa_dfl_app_submitted
    document = app.goods_certificates.first()

    assert document.goods_description == "goods_description value"
    url = CaseURLS.fa_dfl_edit_goods_description(app.pk, document.pk)
    resp = ilb_admin_client.get(url)
    assert resp.status_code == HTTPStatus.OK

    resp = ilb_admin_client.post(url)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {"goods_description": ["You must enter this item"]}

    resp = ilb_admin_client.post(url, data={"goods_description": "New Description"}, follow=True)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {}
    document.refresh_from_db()
    assert document.goods_description == "New Description"


@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_view_goods_certificate_get(mock_get_file_from_s3, fa_dfl_app_submitted, importer_client):
    mock_get_file_from_s3.return_value = b"test_file"
    app = fa_dfl_app_submitted
    document = app.goods_certificates.first()

    url = CaseURLS.fa_dfl_view_goods(app.pk, document.pk)
    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert resp.headers["Content-Disposition"] == 'attachment; filename="dummy-filename"'


def test_delete_goods_certificate(fa_dfl_app_in_progress, importer_client):
    app = fa_dfl_app_in_progress
    assert app.goods_certificates.count() == 1
    document = app.goods_certificates.get()
    assert document.is_active is True

    url = CaseURLS.fa_dfl_delete_goods(app.pk, document.pk)
    resp = importer_client.post(url)
    assert resp.status_code == HTTPStatus.FOUND
    assert resp.headers["Location"] == CaseURLS.fa_dfl_list_goods(app.pk)

    document.refresh_from_db()
    assert document.is_active is False


def test_edit_report_firearms_edit(completed_dfl_app_with_supplementary_report, importer_client):
    app = completed_dfl_app_with_supplementary_report
    report = app.supplementary_info.reports.first()
    report_firearms = report.firearms.first()

    url = CaseURLS.fa_dfl_report_manual_edit(
        app.pk,
        report.pk,
        report_firearms.pk,
    )
    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context["page_title"] == "Edit Firearm Details"

    resp = importer_client.post(url)
    assert resp.context["form"].errors == {
        "calibre": ["You must enter this item"],
        "model": ["You must enter this item"],
        "proofing": ["You must enter this item"],
        "serial_number": ["You must enter this item"],
    }

    resp = importer_client.post(
        url, data={"calibre": "7", "model": "GP", "proofing": "yes", "serial_number": "7"}
    )
    assert resp.status_code == HTTPStatus.FOUND
    report_firearms.refresh_from_db()
    assert report_firearms.calibre == "7"


def test_report_firearms_delete(completed_dfl_app_with_supplementary_report, importer_client):
    app = completed_dfl_app_with_supplementary_report
    report = app.supplementary_info.reports.first()
    assert report.firearms.count() == 1
    report_firearms = report.firearms.first()

    url = CaseURLS.fa_dfl_report_manual_delete(
        app.pk,
        report.pk,
        report_firearms.pk,
    )
    response = importer_client.post(url)
    assert response.status_code == HTTPStatus.FOUND
    assert report.firearms.count() == 0


def test_report_firearms_no_report(completed_dfl_app_with_supplementary_report, importer_client):
    app = completed_dfl_app_with_supplementary_report
    report = app.supplementary_info.reports.first()
    assert report.firearms.count() == 1
    good = app.goods_certificates.first()

    url = CaseURLS.fa_dfl_report_add_no_firearms(app.pk, report.pk, good.pk)
    response = importer_client.post(url)
    assert response.status_code == HTTPStatus.FOUND

    assert report.firearms.count() == 2
    new_report = report.firearms.last()
    assert new_report.is_no_firearm is True


def test_report_firearms_manual_report(
    completed_dfl_app_with_supplementary_report, importer_client
):
    app = completed_dfl_app_with_supplementary_report
    report = app.supplementary_info.reports.first()
    assert report.firearms.count() == 1
    goods_certificate = report.get_goods_certificates().first()

    url = CaseURLS.fa_dfl_report_manual_add(
        app.pk,
        report.pk,
        goods_certificate.pk,
    )
    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context["page_title"] == "Add Firearm Details"

    resp = importer_client.post(
        url, data={"calibre": "7", "model": "GP", "proofing": "yes", "serial_number": "7"}
    )
    assert resp.status_code == HTTPStatus.FOUND
    assert report.firearms.count() == 2
    new_report = report.firearms.last()
    assert new_report.is_no_firearm is False
    assert new_report.is_manual is True

    assert new_report.calibre == "7"
    assert new_report.model == "GP"
    assert new_report.serial_number == "7"
    assert new_report.proofing == "yes"


@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_add_report_firearm_upload(
    mock_get_file_from_s3, completed_dfl_app_with_supplementary_report, importer_client
):
    mock_get_file_from_s3.return_value = b"test_file"
    app = completed_dfl_app_with_supplementary_report
    report = app.supplementary_info.reports.first()
    assert report.firearms.count() == 1
    goods_certificate = report.get_goods_certificates().first()

    url = CaseURLS.fa_dfl_report_upload_add(
        app.pk,
        report.pk,
        goods_certificate.pk,
    )
    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["page_title"] == "Add Firearm Details"

    resp = importer_client.post(url)
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {"file": ["You must enter this item"]}
    resp = importer_client.post(
        url,
        data={"file": SimpleUploadedFile("myimage.png", b"file_content")},
    )
    assert resp.status_code == HTTPStatus.FOUND
    assert report.firearms.count() == 2
    new_report = report.firearms.last()
    assert new_report.is_no_firearm is False
    assert new_report.is_manual is False
    assert new_report.is_upload is True


@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_view_uploaded_document(
    mock_get_file_from_s3, completed_dfl_app_with_supplementary_report, importer_client
):
    app = completed_dfl_app_with_supplementary_report
    mock_get_file_from_s3.return_value = b"test_file"
    report = app.supplementary_info.reports.first()
    goods_certificate = report.get_goods_certificates().first()

    url = CaseURLS.fa_dfl_report_upload_add(app.pk, report.pk, goods_certificate.pk)
    resp = importer_client.post(
        url,
        data={"file": SimpleUploadedFile("myimage.png", b"file_content")},
    )
    assert resp.status_code == HTTPStatus.FOUND

    new_report = report.firearms.last()
    url = CaseURLS.fa_dfl_report_view_document(app.pk, report.pk, new_report.pk)
    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert (
        resp.headers["Content-Disposition"] == 'attachment; filename="original_name: myimage.png"'
    )


class TestDFLGoodsCertificateDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, fa_dfl_app_in_progress):
        self.url = CaseURLS.fa_dfl_list_goods(fa_dfl_app_in_progress.pk)

    def test_permission(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_only(self):
        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_goods_shown(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assertTemplateUsed(response, "web/domains/case/import/fa-dfl/goods-list.html")

        context = response.context
        assert len(context["goods_list"]) == 1

        html = response.content.decode("utf-8")
        assert "Goods Certificates" in html
        assert "Add Goods" in html

    def test_no_goods_shown(self, fa_dfl_app_in_progress):
        fa_dfl_app_in_progress.goods_certificates.all().delete()
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assertTemplateUsed(response, "web/domains/case/import/fa-dfl/goods-list.html")

        context = response.context
        assert len(context["goods_list"]) == 0

        html = response.content.decode("utf-8")
        assert "There are no goods attached" in html
        assert "Add Goods" in html


class TestEditDFLGoodsDescription:
    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_client, fa_dfl_app_submitted):
        self.app = fa_dfl_app_submitted
        self.client = ilb_admin_client

        self.client.post(CaseURLS.take_ownership(self.app.pk, "import"))
        self.app.refresh_from_db()

        self.app.decision = self.app.APPROVE
        self.app.save()

        self.url = CaseURLS.prepare_response(self.app.pk, "import")

    def test_edit_licence_goods(self):
        goods: DFLGoodsCertificate = self.app.goods_certificates.first()

        assert goods.goods_description == "goods_description value"
        assert goods.goods_description_original == "goods_description value"

        resp = self.client.get(self.url)
        assert (
            "<td>goods_description value</td><td>Unlimited</td><td>units</td>"
            in resp.content.decode()
        )

        self.client.post(
            CaseURLS.fa_dfl_edit_goods_description(self.app.pk, goods.pk),
            data={"goods_description": "New Description"},
        )

        goods.refresh_from_db()

        assert goods.goods_description == "New Description"
        assert goods.goods_description_original == "goods_description value"

        resp = self.client.get(self.url)
        assert "<td>New Description</td><td>Unlimited</td><td>units</td>" in resp.content.decode()

    def test_reset_licence_goods(self):
        goods: DFLGoodsCertificate = self.app.goods_certificates.first()

        assert goods.goods_description_original == "goods_description value"

        goods.goods_description = "Override"

        goods.save()
        goods.refresh_from_db()

        resp = self.client.get(self.url)
        assert "<td>Override</td><td>Unlimited</td><td>units</td>" in resp.content.decode()

        self.client.post(
            CaseURLS.fa_dfl_reset_goods_description(self.app.pk, goods.pk),
        )

        goods.refresh_from_db()

        assert goods.goods_description == "goods_description value"
        assert goods.goods_description_original == "goods_description value"

        resp = self.client.get(self.url)
        assert (
            "<td>goods_description value</td><td>Unlimited</td><td>units</td>"
            in resp.content.decode()
        )
