import datetime as dt
from http import HTTPStatus

import pytest
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from web.domains.case._import.nuclear_material.forms import (
    nuclear_material_available_commodities,
    nuclear_material_available_units,
)
from web.domains.case.shared import ImpExpStatus
from web.forms.fields import JQUERY_DATE_FORMAT
from web.mail.constants import EmailTypes
from web.mail.url_helpers import (
    get_case_manage_view_url,
    get_validate_digital_signatures_url,
)
from web.models import (
    Commodity,
    Country,
    ImportApplicationType,
    NuclearMaterialApplication,
    NuclearMaterialApplicationGoods,
    Task,
    UpdateRequest,
)
from web.sites import SiteName, get_caseworker_site_domain
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.helpers import (
    CaseURLS,
    check_gov_notify_email_was_sent,
    check_page_errors,
)
from web.utils.validation import ApplicationErrors, PageErrors


class TestNuclearMaterialApplicationCreateView(AuthTestCase):
    url = reverse_lazy("import:create-nuclear")
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

        self.importer_client.post(
            self.url,
            data={"importer": self.importer.pk, "importer_office": self.importer_office.pk},
        )
        application = NuclearMaterialApplication.objects.get()
        assert application.process_type == NuclearMaterialApplication.PROCESS_TYPE

        application_type = application.application_type
        assert application_type.type == ImportApplicationType.Types.NMIL

        task = application.tasks.get()
        assert task.task_type == Task.TaskType.PREPARE
        assert task.is_active is True

    def test_anonymous_post_access_redirects(self):
        response = self.anonymous_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

    def test_forbidden_post_access(self):
        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestNuclearMaterialApplicationApplicantDetails(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.process = NuclearMaterialApplication.objects.create(
            process_type=NuclearMaterialApplication.PROCESS_TYPE,
            application_type=ImportApplicationType.objects.get(
                type=ImportApplicationType.Types.NMIL
            ),
            status=ImpExpStatus.IN_PROGRESS,
            importer=self.importer,
            created_by=self.importer_user,
            last_updated_by=self.importer_user,
        )

        Task.objects.create(process=self.process, task_type=Task.TaskType.PREPARE)
        self.url = reverse("import:nuclear:edit", kwargs={"application_pk": self.process.pk})
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

        self.valid_country = Country.util.get_all_countries().get(name="Iran")

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)

        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_logged_in_permissions(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_content(self):
        response = self.importer_client.get(self.url)
        assert self.importer.name in response.content.decode()

    def test_save_application_details(self):
        app_ref = "REF64563343"
        consignor_name = "Exporter Name"
        consignor_address = "Exporter Address"

        data = {
            "contact": self.importer_user.pk,
            "applicant_reference": app_ref,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "consignor_name": consignor_name,
            "consignor_address": consignor_address,
            "shipment_start_date": dt.date.today().strftime(JQUERY_DATE_FORMAT),
        }
        self.importer_client.post(
            reverse("import:nuclear:edit", kwargs={"application_pk": self.process.pk}),
            data=data,
        )

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        application = NuclearMaterialApplication.objects.get(pk=self.process.pk)
        assert application.contact == self.importer_user
        assert application.applicant_reference == app_ref
        assert application.origin_country == self.valid_country
        assert application.consignment_country == self.valid_country
        assert application.consignor_name == consignor_name
        assert application.consignor_address == consignor_address


class TestNuclearMaterialGoodsDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, nuclear_app_in_progress):
        self.url = reverse(
            "import:nuclear:list-goods", kwargs={"application_pk": nuclear_app_in_progress.pk}
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

        assertTemplateUsed(response, "web/domains/case/import/nuclear_material/goods-list.html")

        context = response.context
        assert len(context["goods_list"]) == 3

        html = response.content.decode("utf-8")
        assert "Nuclear Materials Import Licence Application - Goods" in html
        assert "Add Goods" in html

    def test_no_goods_shown(self, nuclear_app_in_progress):
        nuclear_app_in_progress.nuclear_goods.all().delete()
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assertTemplateUsed(response, "web/domains/case/import/nuclear_material/goods-list.html")

        context = response.context
        assert len(context["goods_list"]) == 0

        html = response.content.decode("utf-8")
        assert "There are no goods attached" in html
        assert "Add Goods" in html


class TestNuclearMaterialApplicationAddEditGoods(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.process = NuclearMaterialApplication.objects.create(
            process_type=NuclearMaterialApplication.PROCESS_TYPE,
            application_type=ImportApplicationType.objects.get(
                type=ImportApplicationType.Types.NMIL
            ),
            status=ImpExpStatus.IN_PROGRESS,
            importer=self.importer,
            created_by=self.importer_user,
            last_updated_by=self.importer_user,
            origin_country=Country.objects.get(name="Belarus"),
        )

        Task.objects.create(process=self.process, task_type=Task.TaskType.PREPARE)

        self.valid_commodity = Commodity.objects.get(commodity_code="2844101000")
        self.goods = NuclearMaterialApplicationGoods.objects.create(
            commodity=self.valid_commodity,
            goods_description="old desc",
            quantity_amount=5,
            quantity_unit=nuclear_material_available_units().first(),
            goods_description_original="old desc",
            quantity_amount_original=5,
            import_application=self.process,
        )

        self.add_url = reverse(
            "import:nuclear:add-goods", kwargs={"application_pk": self.process.pk}
        )
        self.edit_url = reverse(
            "import:nuclear:edit-goods",
            kwargs={"application_pk": self.process.pk, "goods_pk": self.goods.pk},
        )
        self.add_redirect_url = f"{LOGIN_URL}?next={self.add_url}"
        self.edit_redirect_url = f"{LOGIN_URL}?next={self.edit_url}"

    def test_add_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.add_url)

        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.add_redirect_url)

    def test_add_forbidden_access(self):
        response = self.exporter_client.get(self.add_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_add_logged_in_permissions(self):
        response = self.importer_client.get(self.add_url)
        assert response.status_code == HTTPStatus.OK

    def test_add_page_content(self):
        response = self.importer_client.get(self.add_url)
        assert response.status_code == HTTPStatus.OK
        page_contents = response.content.decode()

        # Header
        assert "Nuclear Materials Import Licence Application" in page_contents
        assert "In Progress" in page_contents
        assert self.importer.name in page_contents

    def test_add_goods(self):
        assert NuclearMaterialApplicationGoods.objects.count() == 1

        data = {
            "commodity": self.valid_commodity.pk,
            "goods_description": "test desc",
            "quantity_amount": 5,
            "quantity_unit": nuclear_material_available_units().first().pk,
        }
        response = self.importer_client.post(
            reverse("import:nuclear:add-goods", kwargs={"application_pk": self.process.pk}),
            data=data,
        )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "import:nuclear:list-goods", kwargs={"application_pk": self.process.pk}
        )
        assert NuclearMaterialApplicationGoods.objects.count() == 2

    def test_edit_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.edit_url)

        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.edit_redirect_url)

    def test_edit_forbidden_access(self):
        response = self.exporter_client.get(self.edit_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_edit_logged_in_permissions(self):
        response = self.importer_client.get(self.edit_url)
        assert response.status_code == HTTPStatus.OK

    def test_edit_page_content(self):
        response = self.importer_client.get(self.edit_url)
        assert response.status_code == HTTPStatus.OK
        page_contents = response.content.decode()

        # Header
        assert "Nuclear Materials Import Licence Application" in page_contents
        assert "In Progress" in page_contents
        assert self.importer.name in page_contents

    def test_edit_goods(self):
        assert NuclearMaterialApplicationGoods.objects.count() == 1

        valid_unit = nuclear_material_available_units().first()
        goods = NuclearMaterialApplicationGoods.objects.create(
            commodity=self.valid_commodity,
            goods_description="old desc",
            quantity_amount=5,
            quantity_unit=valid_unit,
            goods_description_original="old desc",
            quantity_amount_original=5,
            import_application=self.process,
        )
        data = {
            "commodity": self.valid_commodity.pk,
            "goods_description": "updated desc",
            "quantity_amount": 10,
            "quantity_unit": valid_unit.pk,
        }
        response = self.importer_client.post(
            reverse(
                "import:nuclear:edit-goods",
                kwargs={"application_pk": self.process.pk, "goods_pk": goods.pk},
            ),
            data=data,
        )

        assert response.status_code == HTTPStatus.FOUND

        assert response.url == reverse(
            "import:nuclear:list-goods", kwargs={"application_pk": self.process.pk}
        )
        assert NuclearMaterialApplicationGoods.objects.count() == 2

        good = NuclearMaterialApplicationGoods.objects.latest("pk")
        assert good.commodity == self.valid_commodity
        assert good.goods_description == "updated desc"
        assert good.quantity_amount == 10

    def test_delete_goods(self):
        goods = NuclearMaterialApplicationGoods.objects.create(
            commodity=self.valid_commodity,
            goods_description="desc",
            quantity_amount=5,
            quantity_unit=nuclear_material_available_units().first(),
            goods_description_original="desc",
            quantity_amount_original=5,
            import_application=self.process,
        )
        assert len(NuclearMaterialApplicationGoods.objects.all()) == 2
        data = {"action": "delete", "item": goods.pk}
        response = self.importer_client.post(
            reverse(
                "import:nuclear:delete-goods",
                kwargs={"application_pk": self.process.pk, "goods_pk": goods.pk},
            ),
            data=data,
        )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "import:nuclear:list-goods", kwargs={"application_pk": self.process.pk}
        )
        assert len(NuclearMaterialApplicationGoods.objects.all()) == 1


class TestNuclearMaterialSupportingDocumentsDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, nuclear_app_in_progress):
        self.url = reverse(
            "import:nuclear:list-documents",
            kwargs={"application_pk": nuclear_app_in_progress.pk},
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

        assertTemplateUsed(
            response, "web/domains/case/import/nuclear_material/supporting-documents-list.html"
        )

        context = response.context
        assert len(context["supporting_documents"]) == 1

        html = response.content.decode("utf-8")
        assert "Nuclear Materials Import Licence Application - Supporting Documents" in html
        assert "Add Supporting Document" in html

    def test_no_goods_shown(self, nuclear_app_in_progress):
        nuclear_app_in_progress.supporting_documents.all().delete()
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assertTemplateUsed(
            response, "web/domains/case/import/nuclear_material/supporting-documents-list.html"
        )

        context = response.context
        assert len(context["supporting_documents"]) == 0

        html = response.content.decode("utf-8")
        assert "There are no supporting documents attached" in html
        assert "Add Supporting Document" in html


class TestSubmitNuclearMaterial:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, nuclear_app_in_progress):
        self.app = nuclear_app_in_progress
        self.client = importer_client
        self.url = reverse("import:nuclear:submit-nuclear", kwargs={"application_pk": self.app.pk})

    def test_submit_catches_duplicate_commodities(self):
        available_commodities = nuclear_material_available_commodities()
        commodity = available_commodities.first()
        another_commodity = available_commodities.last()

        self.app.nuclear_goods.all().delete()
        self.app.nuclear_goods.create(
            commodity=commodity,
            goods_description="Goods 1",
            quantity_amount=1,
            quantity_unit=nuclear_material_available_units().first(),
            goods_description_original="Goods 1",
            quantity_amount_original=1,
        )

        self.app.nuclear_goods.create(
            commodity=commodity,
            goods_description="Goods 2 (dupe)",
            quantity_amount=1,
            quantity_unit=nuclear_material_available_units().first(),
            goods_description_original="Goods 2 (dupe)",
            quantity_amount_original=1,
        )

        self.app.nuclear_goods.create(
            commodity=another_commodity,
            goods_description="Goods 3",
            quantity_amount=1,
            quantity_unit=nuclear_material_available_units().first(),
            goods_description_original="Goods 3",
            quantity_amount_original=1,
        )

        response = self.client.get(self.url)

        errors: ApplicationErrors = response.context["errors"]
        check_page_errors(errors, "Application Details", ["Goods - Commodity Code"])

        page_errors: PageErrors = errors.get_page_errors("Application Details")
        assert page_errors.errors[0].field_name == "Goods - Commodity Code"
        assert page_errors.errors[0].messages == [
            f"Duplicate commodity codes. Please ensure these codes are only listed once: {commodity.commodity_code}."
        ]

    def test_submit_catches_invalid_commodity(self):
        invalid_commodity = Commodity.objects.get(commodity_code="0306141000")

        self.app.nuclear_goods.all().delete()
        # Add an invalid commodity
        self.app.nuclear_goods.create(
            commodity=invalid_commodity,
            goods_description="Goods 1",
            quantity_amount=1,
            quantity_unit=nuclear_material_available_units().first(),
            goods_description_original="Goods 1",
            quantity_amount_original=1,
        )

        response = self.client.get(self.url)

        errors: ApplicationErrors = response.context["errors"]
        check_page_errors(errors, "Application Details", ["Goods - Commodity Code"])

        page_errors: PageErrors = errors.get_page_errors("Application Details")
        assert page_errors.errors[0].field_name == "Goods - Commodity Code"
        assert page_errors.errors[0].messages == [
            f"Commodity '{invalid_commodity.commodity_code}' is invalid."
        ]

    def test_submit_nuclear_closes_open_update_request(self, ilb_admin_user, importer_one_contact):
        # Add a fake update request.
        self.app.update_requests.create(
            status=UpdateRequest.Status.UPDATE_IN_PROGRESS,
            request_subject="request_subject value",
            request_detail="request_detail value",
            response_detail="response_detail value",
            request_datetime=timezone.now(),
            requested_by=ilb_admin_user,
            response_datetime=timezone.now(),
            response_by=importer_one_contact,
        )
        # Set the case officer (to fake them being the person who initiated the update request.
        self.app.case_owner = ilb_admin_user
        self.app.save()

        self.client.post(self.url, data={"confirmation": "I AGREE"})

        self.app.refresh_from_db()
        check_gov_notify_email_was_sent(
            1,
            ["ilb_admin_user@example.com"],  # /PS-IGNORE
            EmailTypes.APPLICATION_UPDATE_RESPONSE,
            {
                "reference": self.app.reference,
                "validate_digital_signatures_url": get_validate_digital_signatures_url(
                    get_caseworker_site_domain()
                ),
                "application_url": get_case_manage_view_url(self.app),
                "icms_url": get_caseworker_site_domain(),
                "service_name": SiteName.CASEWORKER.label,
            },
        )


class TestEditNuclearLicenceGoods:
    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_client, nuclear_app_submitted):
        self.app = nuclear_app_submitted
        self.client = ilb_admin_client

        self.client.post(CaseURLS.take_ownership(self.app.pk, "import"))
        self.app.refresh_from_db()

        self.app.decision = self.app.APPROVE
        self.app.save()

        self.url = CaseURLS.prepare_response(self.app.pk, "import")

    def test_edit_licence_goods(self):
        goods: NuclearMaterialApplicationGoods = self.app.nuclear_goods.first()

        assert goods.goods_description == "Test Goods"
        assert goods.quantity_amount == 1000

        assert goods.goods_description_original == "Test Goods"
        assert goods.quantity_amount_original == 1000

        resp = self.client.get(self.url)

        assert "<td>Test Goods</td><td>1000.000</td><td>Kilogramme</td>" in resp.content.decode()

        response = self.client.post(
            reverse(
                "import:nuclear:edit-goods-licence",
                kwargs={"application_pk": self.app.pk, "goods_pk": goods.pk},
            ),
            data={
                "goods_description": "New Description",
                "quantity_amount": 99.000,
                "quantity_unit": goods.quantity_unit.pk,
            },
        )
        assert response.status_code == 302

        goods.refresh_from_db()

        assert goods.goods_description == "New Description"
        assert goods.quantity_amount == 99

        assert goods.goods_description_original == "Test Goods"
        assert goods.quantity_amount_original == 1000

        resp = self.client.get(self.url)
        assert "<td>New Description</td><td>99.000</td><td>Kilogramme</td>" in resp.content.decode()

    def test_reset_licence_goods(self):
        goods: NuclearMaterialApplicationGoods = self.app.nuclear_goods.first()

        assert goods.goods_description_original == "Test Goods"
        assert goods.quantity_amount_original == 1000

        goods.goods_description = "Override"
        goods.quantity_amount = 50

        goods.save()
        goods.refresh_from_db()

        resp = self.client.get(self.url)
        assert "<td>Override</td><td>50.000</td><td>Kilogramme</td>" in resp.content.decode()

        self.client.post(
            reverse(
                "import:nuclear:reset-goods-licence",
                kwargs={"application_pk": self.app.pk, "goods_pk": goods.pk},
            ),
        )

        goods.refresh_from_db()

        assert goods.goods_description == "Test Goods"
        assert goods.quantity_amount == 1000

        assert goods.goods_description_original == "Test Goods"
        assert goods.quantity_amount_original == 1000

        resp = self.client.get(self.url)
        assert "<td>Test Goods</td><td>1000.000</td><td>Kilogramme</td>" in resp.content.decode()
