import datetime as dt
from http import HTTPStatus
from unittest import mock

import pytest
from pytest_django.asserts import assertInHTML, assertTemplateUsed

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.models import SILGoodsSection582Obsolete  # /PS-IGNORE
from web.models import SILGoodsSection582Other  # /PS-IGNORE
from web.models import (
    ImportApplicationLicence,
    Section5Authority,
    SILApplication,
    SILGoodsSection1,
    SILGoodsSection2,
    SILGoodsSection5,
    SILLegacyGoods,
    Task,
    Template,
)
from web.tests.application_utils import create_import_app, save_app_data
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS, check_page_errors
from web.utils.validation import ApplicationErrors, PageErrors


def test_create_fa_sil(importer_client, importer, office):
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-sil",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )

    app = SILApplication.objects.get(pk=app_pk)
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)
    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])


def test_can_edit_application(importer_client, fa_sil_app_in_progress):
    # Test we can save a single field now
    app = fa_sil_app_in_progress
    save_app_data(
        client=importer_client,
        view_name="import:fa-sil:edit",
        app_pk=app.pk,
        form_data={"applicant_reference": "A new value"},
    )

    app.refresh_from_db()
    assert app.applicant_reference == "A new value"


def test_add_section_1_goods(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    add_goods_url = CaseURLS.fa_sil_add_section(app.pk, "section1")
    response = importer_client.post(add_goods_url)
    assert response.status_code == HTTPStatus.OK

    # Unlimited quantity

    data = {
        "manufacture": False,
        "description": "sec 1 goods",
        "quantity": "",
        "unlimited_quantity": "on",
    }
    response = importer_client.post(add_goods_url, data=data)
    assert response.status_code == HTTPStatus.FOUND

    # Specified quantity

    data = {
        "manufacture": False,
        "description": "More sec 1 goods",
        "quantity": 10,
        "unlimited_quantity": "off",
    }
    response = importer_client.post(add_goods_url, data=data)
    assert response.status_code == HTTPStatus.FOUND

    # Invalid quantity data

    data = {
        "manufacture": True,
        "description": "Invalid Sec 1 goods",
        "quantity": "",
        "unlimited_quantity": "",
    }
    response = importer_client.post(add_goods_url, data=data)
    assert response.status_code == HTTPStatus.OK
    assertInHTML(
        '<div class="error-message">You must enter either a quantity or select unlimited quantity</div>',
        response.content.decode("utf-8"),
    )

    app.refresh_from_db()
    assert app.goods_section1.count() == 3


def test_add_section_2_goods(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    add_goods_url = CaseURLS.fa_sil_add_section(app.pk, "section2")

    # Unlimited quantity

    data = {
        "manufacture": False,
        "description": "sec 2 goods",
        "quantity": "",
        "unlimited_quantity": "on",
    }
    response = importer_client.post(add_goods_url, data=data)
    assert response.status_code == HTTPStatus.FOUND

    # Specified quantity

    data = {
        "manufacture": False,
        "description": "More sec 2 goods",
        "quantity": 20,
        "unlimited_quantity": "off",
    }
    response = importer_client.post(add_goods_url, data=data)
    assert response.status_code == HTTPStatus.FOUND

    # Invalid quantity data

    data = {
        "manufacture": False,
        "description": "Invalid Sec 2 goods",
        "quantity": "",
        "unlimited_quantity": "",
    }
    response = importer_client.post(add_goods_url, data=data)
    assert response.status_code == HTTPStatus.OK
    assertInHTML(
        '<div class="error-message">You must enter either a quantity or select unlimited quantity</div>',
        response.content.decode("utf-8"),
    )

    app.refresh_from_db()
    assert app.goods_section2.count() == 3


def test_edit_section_1_goods(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    add_goods_url = CaseURLS.fa_sil_add_section(app.pk, "section1")
    response = importer_client.get(add_goods_url)
    assert response.status_code == HTTPStatus.OK

    data = {
        "manufacture": False,
        "description": "sec 1 goods",
        "quantity": "",
        "unlimited_quantity": "on",
    }
    response = importer_client.post(add_goods_url, data=data)
    assert response.status_code == HTTPStatus.FOUND

    section_1 = app.goods_section1.first()
    url = CaseURLS.fa_sil_edit_section(app.pk, "section1", section_1.pk)
    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK

    data["description"] = "new description"
    response = importer_client.post(url, data=data)
    assert response.status_code == HTTPStatus.FOUND
    section_1.refresh_from_db()
    assert section_1.description == "new description"


def test_delete_section_1_goods(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    add_goods_url = CaseURLS.fa_sil_add_section(app.pk, "section1")
    response = importer_client.get(add_goods_url)
    assert response.status_code == HTTPStatus.OK

    data = {
        "manufacture": False,
        "description": "sec 1 goods",
        "quantity": "",
        "unlimited_quantity": "on",
    }
    response = importer_client.post(add_goods_url, data=data)
    assert response.status_code == HTTPStatus.FOUND
    section_1 = app.goods_section1.first()
    assert section_1.is_active is True

    url = CaseURLS.fa_sil_delete_section(app.pk, "section1", section_1.pk)
    response = importer_client.post(url)
    assert response.status_code == HTTPStatus.FOUND
    section_1.refresh_from_db()
    assert section_1.is_active is False


def test_edit_section_5_goods(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    add_goods_url = CaseURLS.fa_sil_add_section(app.pk, "section5")
    response = importer_client.get(add_goods_url)
    assert response.status_code == HTTPStatus.OK
    html = response.content.decode("utf-8")
    assert "Please choose a subsection" in html


def test_choose_goods_section(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    url = CaseURLS.fa_sil_choose_goods_section(app.pk)
    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert (
        response.context["page_title"]
        == "Firearms and Ammunition (Specific Import Licence) - Edit Goods"
    )
    assert response.context["has_goods"] is True


def test_choose_goods_section_permission_denied(importer_two_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    url = CaseURLS.fa_sil_choose_goods_section(app.pk)
    response = importer_two_client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_validate_query_param_shows_errors(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    app.origin_country = None
    app.save()

    edit_url = CaseURLS.fa_sil_edit(app.pk)

    # No query param so no errors by default
    response = importer_client.get(f"{edit_url}")
    assert response.status_code == HTTPStatus.OK
    form = response.context["form"]
    assert not form.errors

    # Validate every field to check for any errors
    response = importer_client.get(f"{edit_url}?validate")
    assert response.status_code == HTTPStatus.OK
    form = response.context["form"]
    message = form.errors["origin_country"][0]
    assert message == "You must enter this item"


@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_view_section5_document(mock_get_file_from_s3, fa_sil_app_in_progress, importer_client):
    mock_get_file_from_s3.return_value = b"test_file"
    app = fa_sil_app_in_progress
    section_5 = app.user_section5.first()
    url = CaseURLS.fa_sil_view_section_5_document(app.pk, section_5.pk)

    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert mock_get_file_from_s3.called is True


def test_archive_section5_document(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    section_5 = app.user_section5.first()
    assert section_5.is_active is True
    url = CaseURLS.fa_sil_archive_section_5_document(app.pk, section_5.pk)
    response = importer_client.post(url)
    assert response.status_code == HTTPStatus.FOUND
    section_5.refresh_from_db()
    assert section_5.is_active is False


def test_add_verified_section5(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    start_date = dt.date(2020, 2, 16)
    end_date = dt.date(2030, 2, 16)
    section_5 = Section5Authority.objects.create(
        importer=app.importer,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        reference="11/A/D/0001",
    )
    assert app.verified_section5.count() == 0

    url = CaseURLS.fa_sil_add_verified_section_5(app.pk, section_5.pk)
    response = importer_client.post(url)
    assert response.status_code == HTTPStatus.FOUND
    app.refresh_from_db()
    assert app.verified_section5.count() == 1


def test_delete_verified_section5(importer_client, fa_sil_app_in_progress):
    app = fa_sil_app_in_progress
    start_date = dt.date(2020, 2, 16)
    end_date = dt.date(2030, 2, 16)
    section_5 = Section5Authority.objects.create(
        importer=app.importer,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        reference="11/A/D/0001",
    )
    app.verified_section5.add(section_5)
    assert app.verified_section5.count() == 1

    url = CaseURLS.fa_sil_delete_verified_section_5(app.pk, section_5.pk)
    response = importer_client.post(url)
    assert response.status_code == HTTPStatus.FOUND
    app.refresh_from_db()
    assert app.verified_section5.count() == 0


def test_view_verified_section5(fa_sil_app_in_progress, importer_client, importer_two_client):
    app = fa_sil_app_in_progress
    start_date = dt.date(2020, 2, 16)
    end_date = dt.date(2030, 2, 16)
    section_5 = Section5Authority.objects.create(
        importer=app.importer,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        reference="11/A/D/0001",
    )

    url = CaseURLS.fa_sil_view_verified_section_5(app.pk, section_5.pk)

    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert (
        response.context["page_title"]
        == "Firearms and Ammunition (Specific Import Licence) - View Verified Section 5"
    )

    response = importer_two_client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_view_verified_section5_document(
    mock_get_file_from_s3, fa_sil_app_in_progress, importer_one_contact, importer_client
):
    mock_get_file_from_s3.return_value = b"test_file"
    app = fa_sil_app_in_progress
    start_date = dt.date(2020, 2, 16)
    end_date = dt.date(2030, 2, 16)
    section_5 = Section5Authority.objects.create(
        importer=app.importer,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        reference="11/A/D/0001",
    )
    section_5.files.create(
        filename="test_file.pdf",
        content_type="application/pdf",
        file_size=1,
        created_by=importer_one_contact,
    )
    document_pk = section_5.files.first().pk

    url = CaseURLS.fa_sil_verified_section_5_document(app.pk, document_pk)
    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert mock_get_file_from_s3.called is True


def test_view_set_cover_letter(fa_sil_app_submitted, ilb_admin_client):
    app = fa_sil_app_submitted
    url = CaseURLS.fa_sil_set_cover_letter(app.pk)
    response = ilb_admin_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context["page_title"] == "Set Cover Letter"

    assert app.cover_letter_text is None
    template = Template.objects.get(template_code=Template.Codes.COVER_FIREARMS_SIIL)
    data = {"template": template.pk}
    response = ilb_admin_client.post(url, data=data)
    assert response.status_code == HTTPStatus.FOUND
    app.refresh_from_db()
    assert app.cover_letter_text


def test_add_report_firearms_upload(
    completed_sil_app_with_uploaded_supplementary_report, importer_client
):
    app = completed_sil_app_with_uploaded_supplementary_report
    report = app.supplementary_info.reports.first()

    url = CaseURLS.fa_sil_report_firearm_upload_add(
        app.pk, report.pk, app.goods_section1.first().pk, "section1"
    )
    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context["page_title"] == "Add Firearm Details"


def test_edit_report_firearms_edit(
    completed_sil_app_with_uploaded_supplementary_report, importer_client
):
    app = completed_sil_app_with_uploaded_supplementary_report
    report = app.supplementary_info.reports.first()
    section5_firearms = report.section5_firearms.first()

    url = CaseURLS.fa_sil_report_firearm_manual_edit(
        app.pk, report.pk, app.goods_section5.first().pk, "section5", section5_firearms.pk
    )
    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context["page_title"] == "Edit Firearm Details"

    resp = importer_client.post(
        url, data={"calibre": "7", "model": "GP", "proofing": "yes", "serial_number": "7"}
    )
    assert resp.status_code == HTTPStatus.FOUND
    section5_firearms.refresh_from_db()
    assert section5_firearms.calibre == "7"


def test_report_firearms_delete(
    completed_sil_app_with_uploaded_supplementary_report, importer_client
):
    app = completed_sil_app_with_uploaded_supplementary_report
    report = app.supplementary_info.reports.first()
    assert report.section5_firearms.count() == 1
    section5_firearms = report.section5_firearms.first()

    url = CaseURLS.fa_sil_report_firearm_manual_delete(
        app.pk, report.pk, app.goods_section5.first().pk, "section5", section5_firearms.pk
    )
    response = importer_client.post(url)
    assert response.status_code == HTTPStatus.FOUND
    assert report.section5_firearms.count() == 0


def test_report_firearms_no_report(
    completed_sil_app_with_uploaded_supplementary_report, importer_client
):
    app = completed_sil_app_with_uploaded_supplementary_report
    report = app.supplementary_info.reports.first()
    assert report.section5_firearms.count() == 1

    url = CaseURLS.fa_sil_report_firearm_no_firearm_add(
        app.pk, report.pk, app.goods_section5.first().pk, "section5"
    )
    response = importer_client.post(url)
    assert response.status_code == HTTPStatus.FOUND

    assert report.section5_firearms.count() == 2
    new_report = report.section5_firearms.last()
    assert new_report.is_no_firearm is True


def test_report_firearms_manual_report(
    completed_sil_app_with_uploaded_supplementary_report, importer_client
):
    app = completed_sil_app_with_uploaded_supplementary_report
    report = app.supplementary_info.reports.first()
    assert report.section5_firearms.count() == 1

    url = CaseURLS.fa_sil_report_firearm_manual_add(
        app.pk, report.pk, app.goods_section5.first().pk, "section5"
    )
    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.context["page_title"] == "Add Firearm Details"

    resp = importer_client.post(
        url, data={"calibre": "7", "model": "GP", "proofing": "yes", "serial_number": "7"}
    )
    assert resp.status_code == HTTPStatus.FOUND
    assert report.section5_firearms.count() == 2
    new_report = report.section5_firearms.last()
    assert new_report.is_no_firearm is False
    assert new_report.is_manual is True

    assert new_report.calibre == "7"
    assert new_report.model == "GP"
    assert new_report.serial_number == "7"
    assert new_report.proofing == "yes"


@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_view_uploaded_document(
    mock_get_file_from_s3, completed_sil_app_with_uploaded_supplementary_report, importer_client
):
    app = completed_sil_app_with_uploaded_supplementary_report
    mock_get_file_from_s3.return_value = b"test_file"
    report = app.supplementary_info.reports.first()
    section5_firearms = report.section5_firearms.first()

    url = CaseURLS.fa_sil_report_firearm_upload_view(
        app.pk, report.pk, app.goods_section5.first().pk, "section5", section5_firearms.pk
    )
    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert (
        resp.headers["Content-Disposition"] == 'attachment; filename="original_name: section5.png"'
    )


def test_manage_checklist_errors(fa_sil_app_submitted, ilb_admin_client):
    app = fa_sil_app_submitted
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
    manage_checklist = CaseURLS.fa_sil_manage_checklist(app.pk)
    resp = ilb_admin_client.post(manage_checklist, follow=True)
    assert resp.status_code == 200
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
        "authority_cover_items_listed": ["You must enter this item"],
        "quantities_within_authority_restrictions": ["You must enter this item"],
    }


def test_manage_checklist(fa_sil_app_submitted, ilb_admin_client):
    app = fa_sil_app_submitted

    assert not hasattr(app, "checklist")

    manage_checklist = CaseURLS.fa_sil_manage_checklist(app.pk)
    resp = ilb_admin_client.get(manage_checklist)
    assert resp.status_code == 200
    assert (
        resp.context["page_title"]
        == "Firearms and Ammunition (Specific Import Licence) - Checklist"
    )
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
        "authority_cover_items_listed": "yes",
        "quantities_within_authority_restrictions": "no",
    }
    resp = ilb_admin_client.post(manage_checklist, data=post_data, follow=True)
    assert resp.status_code == 200
    assert resp.context["form"].errors == {}


class TestSILGoodsCertificateDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, fa_sil_app_in_progress):
        self.url = CaseURLS.fa_sil_list_goods(fa_sil_app_in_progress.pk)

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

        assertTemplateUsed(response, "web/domains/case/import/fa-sil/goods/list.html")

        html = response.content.decode("utf-8")
        assert "Add Goods Item" in html
        assert "Section 1 goods" in html
        assert "Section 2 goods" in html
        assert "Section 5 goods" in html
        assert "Section 58 obsoletes goods" in html
        assert "Section 58 other goods" in html

    def test_no_goods_shown(self, fa_sil_app_in_progress):
        fa_sil_app_in_progress.goods_section1.all().delete()
        fa_sil_app_in_progress.goods_section2.all().delete()
        fa_sil_app_in_progress.goods_section5.all().delete()
        fa_sil_app_in_progress.goods_section582_obsoletes.all().delete()
        fa_sil_app_in_progress.goods_section582_others.all().delete()

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assertTemplateUsed(response, "web/domains/case/import/fa-sil/goods/list.html")

        html = response.content.decode("utf-8")
        assert "Add Goods Item" in html
        assert "Section 1 goods" not in html
        assert "Section 2 goods" not in html
        assert "Section 5 goods" not in html
        assert "Section 58 obsoletes goods" not in html
        assert "Section 58 other goods" not in html


class TestSILResponsePrepEditGoodsView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, fa_sil_app_submitted):
        self.quantity_section = SILGoodsSection5.objects.get(
            import_application=fa_sil_app_submitted, description="Section 5 goods"
        )
        self.url = CaseURLS.fa_sil_response_prep_edit_goods(
            fa_sil_app_submitted.pk, self.quantity_section.pk, "section5"
        )
        self.url_reset = CaseURLS.fa_sil_response_prep_reset_goods(
            fa_sil_app_submitted.pk, self.quantity_section.pk, "section5"
        )
        self.unlimited_quantity_section = SILGoodsSection5.objects.get(
            import_application=fa_sil_app_submitted, description="Unlimited Section 5 goods"
        )
        self.url_unlimited_quantity = CaseURLS.fa_sil_response_prep_edit_goods(
            fa_sil_app_submitted.pk,
            self.unlimited_quantity_section.pk,
            "section5",
        )

    def test_permission(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.get(self.url_unlimited_quantity)
        assert response.status_code == HTTPStatus.OK

    def test_update_unlimited_quantity_section(self):
        response = self.ilb_admin_client.post(
            self.url_unlimited_quantity,
            data={
                "quantity": "",
                "unlimited_quantity": "on",
                "description": "New unlimited description",
            },
        )
        assert response.status_code == HTTPStatus.FOUND, response.context["form"].errors
        self.unlimited_quantity_section.refresh_from_db()
        assert self.unlimited_quantity_section.description == "New unlimited description"

    def test_update_quantity_section(self):
        response = self.ilb_admin_client.post(
            self.url,
            data={"quantity": 333, "description": "New description"},
        )
        assert response.status_code == HTTPStatus.FOUND, response.context["form"].errors
        self.quantity_section.refresh_from_db()
        assert self.quantity_section.description == "New description"
        assert self.quantity_section.quantity == 333

    def test_update_quantity_section_no_quantity(self):
        response = self.ilb_admin_client.post(
            self.url,
            data={"quantity": "", "description": "New description"},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.context["form"].errors == {"quantity": ["You must enter this item"]}

    def test_reset_data_(self):
        self.ilb_admin_client.post(
            self.url,
            data={"quantity": "999", "description": "New description"},
        )
        self.quantity_section.refresh_from_db()
        assert self.quantity_section.description == "New description"
        assert self.quantity_section.quantity == 999

        self.ilb_admin_client.post(self.url_reset)
        self.quantity_section.refresh_from_db()

        assert self.quantity_section.description == "Section 5 goods"
        assert self.quantity_section.quantity == 333


class TestSubmitFaSIL:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, fa_sil_app_in_progress):
        self.app = fa_sil_app_in_progress
        self.client = importer_client

    def test_submit_catches_incorrect_licence_for(self):
        # The app has a goods line for every section (so let's disable a section)
        self.app.section5 = False
        self.app.save()

        url = CaseURLS.fa_sil_submit(self.app.pk)

        response = self.client.get(url)

        errors: ApplicationErrors = response.context["errors"]
        check_page_errors(errors, "Application Details", ["Firearm Licence For"])

        page_errors: PageErrors = errors.get_page_errors("Application Details")
        page_errors.errors[0].field_name = "Firearm Licence For"
        page_errors.errors[0].messages = [
            "The sections selected here do not match those selected in the goods items."
        ]


def test_fa_sil_app_submitted_has_a_licence(fa_sil_app_submitted):
    assert fa_sil_app_submitted.licences.filter(
        status=ImportApplicationLicence.Status.DRAFT
    ).exists()


def test_sil_upload_firearm_supplementary_report(
    completed_sil_app_with_uploaded_supplementary_report,
):
    supplementary_report = (
        completed_sil_app_with_uploaded_supplementary_report.supplementary_info.reports.get()
    )
    assert len(supplementary_report.get_report_firearms(is_upload=True)) == 5
    assert len(supplementary_report.get_report_firearms(is_upload=False)) == 0

    # Check that the uploaded files are associated with the correct section/good model
    for uploaded_firearm in supplementary_report.get_report_firearms(is_upload=True):
        match uploaded_firearm.section_type:
            case "section1":
                assert isinstance(uploaded_firearm.goods_certificate, SILGoodsSection1)
            case "section2":
                assert isinstance(uploaded_firearm.goods_certificate, SILGoodsSection2)
            case "section5":
                assert isinstance(uploaded_firearm.goods_certificate, SILGoodsSection5)
            case "section582-obsolete":
                assert isinstance(
                    uploaded_firearm.goods_certificate, SILGoodsSection582Obsolete  # /PS-IGNORE
                )
            case "section582-other":
                assert isinstance(
                    uploaded_firearm.goods_certificate, SILGoodsSection582Other  # /PS-IGNORE
                )
            case "section_legacy":
                assert isinstance(uploaded_firearm.goods_certificate, SILLegacyGoods)
            case _:
                assert False, "Unexpected section type"
