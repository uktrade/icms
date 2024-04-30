from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertTemplateUsed

from web.domains.case._import.fa_sil.models import (
    SILGoodsSection582Obsolete,  # /PS-IGNORE
)
from web.domains.case._import.fa_sil.models import SILGoodsSection582Other  # /PS-IGNORE
from web.domains.case._import.fa_sil.models import (
    SILGoodsSection1,
    SILGoodsSection2,
    SILGoodsSection5,
    SILLegacyGoods,
)
from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.models import ImportApplicationLicence, SILApplication, Task
from web.tests.application_utils import create_import_app, save_app_data
from web.tests.auth import AuthTestCase
from web.tests.helpers import check_page_errors
from web.utils.validation import ApplicationErrors, PageErrors

if TYPE_CHECKING:
    from django.test.client import Client


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


class TestEditFirearmsSILApplication:
    client: "Client"
    app: SILApplication

    @pytest.fixture(autouse=True)
    def set_client(self, importer_client):
        self.client = importer_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, importer, office):
        app_pk = create_import_app(
            client=self.client,
            view_name="import:create-fa-sil",
            importer_pk=importer.pk,
            office_pk=office.pk,
        )
        self.app = SILApplication.objects.get(pk=app_pk)

    def test_can_edit_application(self):
        # Test we can save a single field now
        save_app_data(
            client=self.client,
            view_name="import:fa-sil:edit",
            app_pk=self.app.pk,
            form_data={"applicant_reference": "A new value"},
        )

        self.app.refresh_from_db()
        assert self.app.applicant_reference == "A new value"

    def test_add_section_1_goods(self):
        add_goods_url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": self.app.pk, "sil_section_type": "section1"},
        )

        # Unlimited quantity

        data = {
            "manufacture": False,
            "description": "sec 1 goods",
            "quantity": "",
            "unlimited_quantity": "on",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        # Specified quantity

        data = {
            "manufacture": False,
            "description": "More sec 1 goods",
            "quantity": 10,
            "unlimited_quantity": "off",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        # Invalid quantity data

        data = {
            "manufacture": True,
            "description": "Invalid Sec 1 goods",
            "quantity": "",
            "unlimited_quantity": "",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == HTTPStatus.OK
        assertInHTML(
            '<div class="error-message">You must enter either a quantity or select unlimited quantity</div>',
            response.content.decode("utf-8"),
        )

        self.app.refresh_from_db()
        assert self.app.goods_section1.count() == 2

    def test_add_section_2_goods(self):
        add_goods_url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": self.app.pk, "sil_section_type": "section2"},
        )

        # Unlimited quantity

        data = {
            "manufacture": False,
            "description": "sec 2 goods",
            "quantity": "",
            "unlimited_quantity": "on",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        # Specified quantity

        data = {
            "manufacture": False,
            "description": "More sec 2 goods",
            "quantity": 20,
            "unlimited_quantity": "off",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == HTTPStatus.FOUND

        # Invalid quantity data

        data = {
            "manufacture": False,
            "description": "Invalid Sec 2 goods",
            "quantity": "",
            "unlimited_quantity": "",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == HTTPStatus.OK
        assertInHTML(
            '<div class="error-message">You must enter either a quantity or select unlimited quantity</div>',
            response.content.decode("utf-8"),
        )

        self.app.refresh_from_db()
        assert self.app.goods_section2.count() == 2

    def test_validate_query_param_shows_errors(self):
        edit_url = reverse("import:fa-sil:edit", kwargs={"application_pk": self.app.pk})

        # No query param so no errors by default
        response = self.client.get(f"{edit_url}")
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert not form.errors

        # Validate every field to check for any errors
        response = self.client.get(f"{edit_url}?validate")
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        message = form.errors["origin_country"][0]
        assert message == "You must enter this item"


class TestSILGoodsCertificateDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, fa_sil_app_in_progress):
        self.url = reverse(
            "import:fa-sil:list-goods", kwargs={"application_pk": fa_sil_app_in_progress.pk}
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


class TestSubmitFaSIL:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, fa_sil_app_in_progress):
        self.app = fa_sil_app_in_progress
        self.client = importer_client

    def test_submit_catches_incorrect_licence_for(self):
        # The app has a goods line for every section (so let's disable a section)
        self.app.section5 = False
        self.app.save()

        url = reverse("import:fa-sil:submit", kwargs={"application_pk": self.app.pk})

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
