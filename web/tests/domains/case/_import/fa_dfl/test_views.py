import re

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
    ImportApplicationLicence,
    Task,
    User,
)
from web.models.shared import FirearmCommodity
from web.tests.helpers import check_page_errors


def _get_view_url(view_name, kwargs=None):
    return reverse(f"import:fa-dfl:{view_name}", kwargs=kwargs)


@pytest.fixture(autouse=True)
def log_in_test_user(client, test_import_user):
    """Logs in the test_import_user for all tests."""

    assert (
        client.login(username=test_import_user.username, password="test") is True
    ), "Failed to login"


@pytest.fixture
def dfl_app_pk(client, office, importer):
    """Creates a fa-dfl application to be used in tests, also tests the create-fa-dfl endpoint"""

    url = reverse("import:create-fa-dfl")
    post_data = {"importer": importer.pk, "importer_office": office.pk}

    count_before = DFLApplication.objects.all().count()

    resp = client.post(url, post_data)

    assert DFLApplication.objects.all().count() == count_before + 1

    application_pk = re.search(r"\d+", resp.url).group(0)

    expected_url = _get_view_url("edit", {"application_pk": application_pk})
    assertRedirects(resp, expected_url, 302)

    return application_pk


def test_edit_dfl_get(client, dfl_app_pk):
    url = _get_view_url("edit", {"application_pk": dfl_app_pk})

    response = client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Edit",
        status_code=200,
    )


def test_validate_query_param_shows_errors(client, dfl_app_pk):
    url = _get_view_url("edit", {"application_pk": dfl_app_pk})

    response = client.get(url)
    assert response.status_code == 200
    form = response.context["form"]
    assert not form.errors

    response = client.get(f"{url}?validate")
    assert response.status_code == 200

    assertFormError(response.context["form"], "proof_checked", "You must enter this item")
    assertFormError(response.context["form"], "origin_country", "You must enter this item")
    assertFormError(response.context["form"], "consignment_country", "You must enter this item")
    assertFormError(response.context["form"], "contact", "You must enter this item")
    assertFormError(response.context["form"], "constabulary", "You must enter this item")


def test_edit_dfl_post_valid(client, dfl_app_pk, importer_contact):
    url = _get_view_url("edit", {"application_pk": dfl_app_pk})

    dfl_countries = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    )
    origin_country = dfl_countries[0]
    consignment_country = dfl_countries[1]
    constabulary = Constabulary.objects.first()

    form_data = {
        "applicant_reference": "applicant_reference value",
        "deactivated_firearm": True,
        "proof_checked": True,
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "contact": importer_contact.pk,
        "commodity_code": FirearmCommodity.EX_CHAPTER_93.value,
        "constabulary": constabulary.pk,
    }
    response = client.post(url, form_data)

    assertRedirects(response, url, 302)

    # check the data has been saved:
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)
    assert dfl_app.applicant_reference == "applicant_reference value"
    assert dfl_app.deactivated_firearm is True
    assert dfl_app.proof_checked is True
    assert dfl_app.origin_country.pk == origin_country.pk
    assert dfl_app.consignment_country.pk == consignment_country.pk
    assert dfl_app.contact.pk == importer_contact.pk
    assert dfl_app.commodity_code == FirearmCommodity.EX_CHAPTER_93.value
    assert dfl_app.constabulary.pk == constabulary.pk


def test_add_goods_document_get(client, dfl_app_pk):
    url = _get_view_url("add-goods", kwargs={"application_pk": dfl_app_pk})

    response = client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Add Goods Certificate",
        status_code=200,
    )


def test_add_goods_document_post_invalid(client, dfl_app_pk):
    url = _get_view_url("add-goods", kwargs={"application_pk": dfl_app_pk})

    form_data = {"foo": "bar"}
    response = client.post(url, form_data)

    assertFormError(response.context["form"], "goods_description", "You must enter this item")
    assertFormError(
        response.context["form"], "deactivated_certificate_reference", "You must enter this item"
    )
    assertFormError(response.context["form"], "issuing_country", "You must enter this item")
    assertFormError(response.context["form"], "document", "You must enter this item")


def test_add_goods_document_post_valid(client, dfl_app_pk):
    url = _get_view_url("add-goods", kwargs={"application_pk": dfl_app_pk})

    issuing_country = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    ).first()
    goods_file = SimpleUploadedFile("myimage.png", b"file_content")

    form_data = {
        "goods_description": "goods_description value",
        "deactivated_certificate_reference": "deactivated_certificate_reference value",
        "issuing_country": issuing_country.pk,
        "document": goods_file,
    }

    response = client.post(url, form_data)

    assertRedirects(response, _get_view_url("edit", {"application_pk": dfl_app_pk}), 302)

    # Check the record has a file
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)

    assert dfl_app.goods_certificates.count() == 1

    goods_cert = dfl_app.goods_certificates.first()
    assert goods_cert.goods_description == "goods_description value"
    assert goods_cert.deactivated_certificate_reference == "deactivated_certificate_reference value"
    assert goods_cert.issuing_country.pk == issuing_country.pk
    assert goods_cert.is_active is True
    assert goods_cert.path == "myimage.png"
    assert goods_cert.filename == "original_name: myimage.png"
    assert goods_cert.content_type == "text/plain"
    assert goods_cert.file_size == goods_file.size


def test_edit_goods_certificate_get(client, dfl_app_pk):
    document_pk = _create_goods_cert(dfl_app_pk)
    url = _get_view_url(
        "edit-goods", kwargs={"application_pk": dfl_app_pk, "document_pk": document_pk}
    )

    response = client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Edit Goods Certificate",
        status_code=200,
    )


def test_edit_goods_certificate_post_invalid(client, dfl_app_pk):
    document_pk = _create_goods_cert(dfl_app_pk)
    url = _get_view_url(
        "edit-goods", kwargs={"application_pk": dfl_app_pk, "document_pk": document_pk}
    )

    form_data = {
        "goods_description": "",
        "deactivated_certificate_reference": "",
        "issuing_country": -1,
    }
    response = client.post(url, form_data)

    assertFormError(
        response.context["form"], "deactivated_certificate_reference", "You must enter this item"
    )
    assertFormError(
        response.context["form"],
        "issuing_country",
        "Select a valid choice. That choice is not one of the available choices.",
    )
    assertFormError(response.context["form"], "goods_description", "You must enter this item")


def test_edit_goods_certificate_post_valid(client, dfl_app_pk):
    document_pk = _create_goods_cert(dfl_app_pk)
    url = _get_view_url(
        "edit-goods", kwargs={"application_pk": dfl_app_pk, "document_pk": document_pk}
    )

    issuing_country = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    ).first()

    form_data = {
        "goods_description": "New goods description",
        "deactivated_certificate_reference": "New deactived certificate reference",
        "issuing_country": issuing_country.pk,
    }
    response = client.post(url, form_data)

    assertRedirects(response, _get_view_url("edit", {"application_pk": dfl_app_pk}), 302)

    # Check the record has a file
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)

    assert dfl_app.goods_certificates.count() == 1

    goods_cert = dfl_app.goods_certificates.first()
    assert goods_cert.goods_description == "New goods description"
    assert goods_cert.deactivated_certificate_reference == "New deactived certificate reference"
    assert goods_cert.issuing_country.pk == issuing_country.pk


def _create_goods_cert(dfl_app_pk):
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)
    issuing_country = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    ).first()
    dfl_app.goods_certificates.create(
        filename="test-file.txt",
        goods_description="goods_description value",
        deactivated_certificate_reference="deactivated_certificate_reference value",
        issuing_country=issuing_country,
        file_size=1024,
        created_by=User.objects.get(username="test_import_user"),
    )
    document_pk = dfl_app.goods_certificates.first().pk

    return document_pk


def test_submit_dfl_get(client, dfl_app_pk):
    url = _get_view_url("submit", kwargs={"application_pk": dfl_app_pk})

    response = client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Submit Application",
        status_code=200,
    )

    assertTemplateUsed(response, "web/domains/case/import/import-case-submit.html")

    # check the errors are displayed in the response
    errors = response.context["errors"]

    check_page_errors(
        errors,
        "Application details",
        [
            "Proof Checked",
            "Country Of Origin",
            "Country Of Consignment",
            "Contact",
            "Constabulary",
        ],
    )

    check_page_errors(errors, "Goods Certificates", ["Goods Certificate"])

    check_page_errors(
        errors,
        "Details of who bought from",
        ["Do you know who you plan to buy/obtain these items from?"],
    )


def test_submit_dfl_post_invalid(client, dfl_app_pk, importer_contact):
    submit_url = _get_view_url("submit", kwargs={"application_pk": dfl_app_pk})

    form_data = {"foo": "bar"}

    response = client.post(submit_url, form_data)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Submit Application",
        status_code=200,
    )

    errors = response.context["errors"]

    check_page_errors(
        errors,
        "Application details",
        [
            "Proof Checked",
            "Country Of Origin",
            "Country Of Consignment",
            "Contact",
            "Constabulary",
        ],
    )

    check_page_errors(errors, "Goods Certificates", ["Goods Certificate"])

    check_page_errors(
        errors,
        "Details of who bought from",
        ["Do you know who you plan to buy/obtain these items from?"],
    )

    assertFormError(response.context["form"], "confirmation", "You must enter this item")

    form_data = {"confirmation": "I will NEVER agree"}
    response = client.post(submit_url, form_data)

    assertFormError(
        response.context["form"], "confirmation", "Please agree to the declaration of truth."
    )

    # Test the know bought from check
    dfl_countries = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    )
    origin_country = dfl_countries[0]
    consignment_country = dfl_countries[1]
    constabulary = Constabulary.objects.first()

    form_data = {
        "applicant_reference": "applicant_reference value",
        "deactivated_firearm": True,
        "proof_checked": True,
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "contact": importer_contact.pk,
        "commodity_code": FirearmCommodity.EX_CHAPTER_93.value,
        "constabulary": constabulary.pk,
    }
    edit_url = _get_view_url("edit", {"application_pk": dfl_app_pk})
    client.post(edit_url, form_data)

    # Save the know bought from to make the application valid.
    form_data = {"know_bought_from": True}
    client.post(
        reverse("import:fa:manage-import-contacts", kwargs={"application_pk": dfl_app_pk}),
        form_data,
    )

    # now we have a valid application submit the application again to see the know_bought_from error
    response = client.post(submit_url, form_data)
    errors = response.context["errors"]
    check_page_errors(errors, "Details of who bought from", ["Person"])


def test_submit_dfl_post_valid(client, dfl_app_pk, importer_contact):
    """Test the full happy path.

    Create the main application
    create a document
    Save the know bought from value
    submit the application
    """

    edit_url = _get_view_url("edit", {"application_pk": dfl_app_pk})
    add_goods_url = _get_view_url("add-goods", kwargs={"application_pk": dfl_app_pk})
    know_bought_from_url = reverse(
        "import:fa:manage-import-contacts", kwargs={"application_pk": dfl_app_pk}
    )
    submit_url = _get_view_url("submit", kwargs={"application_pk": dfl_app_pk})

    dfl_countries = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    )
    origin_country = dfl_countries[0]
    consignment_country = dfl_countries[1]
    constabulary = Constabulary.objects.first()

    form_data = {
        "applicant_reference": "applicant_reference value",
        "deactivated_firearm": True,
        "proof_checked": True,
        "origin_country": origin_country.pk,
        "consignment_country": consignment_country.pk,
        "contact": importer_contact.pk,
        "commodity_code": FirearmCommodity.EX_CHAPTER_93.value,
        "constabulary": constabulary.pk,
        "know_bought_from": False,
    }

    # Save the main application
    client.post(edit_url, form_data)

    issuing_country = Country.objects.filter(
        country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
    ).first()
    goods_file = SimpleUploadedFile("myimage.png", b"file_content")

    form_data = {
        "goods_description": "goods_description value",
        "deactivated_certificate_reference": "deactivated_certificate_reference value",
        "issuing_country": issuing_country.pk,
        "document": goods_file,
    }

    # Save the goods certificate
    client.post(add_goods_url, form_data)

    # Save the know bought from
    form_data = {"know_bought_from": False}
    client.post(know_bought_from_url, form_data)

    form_data = {"confirmation": "I AGREE"}
    response = client.post(submit_url, form_data)

    assertRedirects(response, reverse("workbasket"), 302)

    # check the application is in the correct state
    application = DFLApplication.objects.get(pk=dfl_app_pk)

    case_progress.check_expected_status(application, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(application, Task.TaskType.PROCESS)

    # And it has a draft licence
    assert application.licences.filter(status=ImportApplicationLicence.Status.DRAFT).exists()


# def test_edit_goods_certificate_description_get(admin_cl, complete_dfl_app_pk):
#     ...
#
#
# def test_edit_goods_certificate_description_post_invalid(admin_client):
#     ...
#
#
# def test_edit_goods_certificate_description_post_valid():
#     ...
#
# def test_view_goods_certificate_get():
#     ...
#
#
# def test_view_goods_certificate_post_invalid():
#     ...
#
#
# def test_view_goods_certificate_post_valid():
#     ...
#
#
# def test_delete_goods_certificate_get():
#     ...
#
#
# def test_delete_goods_certificate_post_invalid():
#     ...
#
#
# def test_delete_goods_certificate_post_valid():
#     ...
