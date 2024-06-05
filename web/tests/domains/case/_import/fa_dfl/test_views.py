import re
from http import HTTPStatus

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
from web.tests.auth import AuthTestCase
from web.tests.helpers import check_page_errors, get_test_client


def _get_view_url(view_name, kwargs=None):
    return reverse(f"import:fa-dfl:{view_name}", kwargs=kwargs)


@pytest.fixture
def dfl_app_pk(importer_client, office, importer):
    """Creates a fa-dfl application to be used in tests, also tests the create-fa-dfl endpoint"""

    url = reverse("import:create-fa-dfl")
    post_data = {"importer": importer.pk, "importer_office": office.pk}

    count_before = DFLApplication.objects.all().count()

    resp = importer_client.post(url, post_data)

    assert DFLApplication.objects.all().count() == count_before + 1

    application_pk = re.search(r"\d+", resp.url).group(0)

    expected_url = _get_view_url("edit", {"application_pk": application_pk})
    assertRedirects(resp, expected_url, HTTPStatus.FOUND)

    return application_pk


def test_edit_dfl_get(
    dfl_app_pk, importer_client, exporter_client, importer_two_contact, importer_site
):
    url = _get_view_url("edit", {"application_pk": dfl_app_pk})

    response = importer_client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Edit",
        status_code=HTTPStatus.OK,
    )

    # Check permissions
    # Exporter can't access it
    response = exporter_client.get(url)
    assert response.status_code == 403

    # A different importer can't access it
    importer_two_client = get_test_client(importer_site.domain, importer_two_contact)
    response = importer_two_client.get(url)
    assert response.status_code == 403


def test_validate_query_param_shows_errors(dfl_app_pk, importer_client):
    url = _get_view_url("edit", {"application_pk": dfl_app_pk})

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


def test_edit_dfl_post_valid(dfl_app_pk, importer_client, importer_one_contact):
    url = _get_view_url("edit", {"application_pk": dfl_app_pk})

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


def test_add_goods_document_get(dfl_app_pk, importer_client):
    url = _get_view_url("add-goods", kwargs={"application_pk": dfl_app_pk})

    response = importer_client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Add Goods Certificate",
        status_code=HTTPStatus.OK,
    )


def test_add_goods_document_post_invalid(dfl_app_pk, importer_client):
    url = _get_view_url("add-goods", kwargs={"application_pk": dfl_app_pk})

    form_data = {"foo": "bar"}
    response = importer_client.post(url, form_data)

    assertFormError(response.context["form"], "goods_description", "You must enter this item")
    assertFormError(
        response.context["form"], "deactivated_certificate_reference", "You must enter this item"
    )
    assertFormError(response.context["form"], "issuing_country", "You must enter this item")
    assertFormError(response.context["form"], "document", "You must enter this item")


def test_add_goods_document_post_valid(dfl_app_pk, importer_client):
    url = _get_view_url("add-goods", kwargs={"application_pk": dfl_app_pk})

    issuing_country = Country.app.get_fa_dfl_issuing_countries().first()
    goods_file = SimpleUploadedFile("myimage.png", b"file_content")

    form_data = {
        "goods_description": "goods_description value",
        "deactivated_certificate_reference": "deactivated_certificate_reference value",
        "issuing_country": issuing_country.pk,
        "document": goods_file,
    }

    response = importer_client.post(url, form_data)

    assertRedirects(
        response, _get_view_url("list-goods", {"application_pk": dfl_app_pk}), HTTPStatus.FOUND
    )

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


def test_edit_goods_certificate_get(dfl_app_pk, importer_client):
    document_pk = _create_goods_cert(dfl_app_pk)
    url = _get_view_url(
        "edit-goods", kwargs={"application_pk": dfl_app_pk, "document_pk": document_pk}
    )

    response = importer_client.get(url)

    assertContains(
        response,
        "Firearms and Ammunition (Deactivated Firearms Licence) - Edit Goods Certificate",
        status_code=HTTPStatus.OK,
    )


def test_edit_goods_certificate_post_invalid(dfl_app_pk, importer_client):
    document_pk = _create_goods_cert(dfl_app_pk)
    url = _get_view_url(
        "edit-goods", kwargs={"application_pk": dfl_app_pk, "document_pk": document_pk}
    )

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


def test_edit_goods_certificate_post_valid(dfl_app_pk, importer_client):
    document_pk = _create_goods_cert(dfl_app_pk)
    url = _get_view_url(
        "edit-goods", kwargs={"application_pk": dfl_app_pk, "document_pk": document_pk}
    )

    issuing_country = Country.app.get_fa_dfl_issuing_countries().first()
    form_data = {
        "goods_description": "New goods description",
        "deactivated_certificate_reference": "New deactived certificate reference",
        "issuing_country": issuing_country.pk,
    }
    response = importer_client.post(url, form_data)

    assertRedirects(
        response, _get_view_url("list-goods", {"application_pk": dfl_app_pk}), HTTPStatus.FOUND
    )

    # Check the record has a file
    dfl_app = DFLApplication.objects.get(pk=dfl_app_pk)

    assert dfl_app.goods_certificates.count() == 1

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


class TestDFLGoodsCertificateDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, fa_dfl_app_in_progress):
        self.url = reverse(
            "import:fa-dfl:list-goods", kwargs={"application_pk": fa_dfl_app_in_progress.pk}
        )

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


def test_submit_dfl_get(dfl_app_pk, importer_client):
    url = _get_view_url("submit", kwargs={"application_pk": dfl_app_pk})

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


def test_submit_dfl_post_invalid(dfl_app_pk, importer_client, importer_one_contact):
    submit_url = _get_view_url("submit", kwargs={"application_pk": dfl_app_pk})

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
    edit_url = _get_view_url("edit", {"application_pk": dfl_app_pk})
    importer_client.post(edit_url, form_data)

    # Save the know bought from to make the application valid.
    form_data = {"know_bought_from": True}
    importer_client.post(
        reverse("import:fa:manage-import-contacts", kwargs={"application_pk": dfl_app_pk}),
        form_data,
    )

    # now we have a valid application submit the application again to see the know_bought_from error
    response = importer_client.post(submit_url, form_data)
    errors = response.context["errors"]
    check_page_errors(errors, "Application Details - Details of Who Bought From", ["Person"])


def test_submit_dfl_post_valid(dfl_app_pk, importer_client, importer_one_contact):
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
