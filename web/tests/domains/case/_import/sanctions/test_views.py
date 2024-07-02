from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from web.models import (
    Commodity,
    Country,
    ImportApplicationType,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
    Task,
)
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.domains.case._import.factory import (
    SanctionsAndAdhocApplicationGoodsFactory,
    SanctionsAndAdhocLicenseApplicationFactory,
)
from web.tests.helpers import check_page_errors
from web.utils.commodity import get_usage_commodities, get_usage_records
from web.utils.validation import ApplicationErrors, PageErrors


class TestSanctionsAndAdhocImportAppplicationCreateView(AuthTestCase):
    url = "/import/create/sanctions/"
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
            reverse("import:create-sanctions"),
            data={"importer": self.importer.pk, "importer_office": self.importer_office.pk},
        )
        application = SanctionsAndAdhocApplication.objects.get()
        assert application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE

        application_type = application.application_type
        assert application_type.type == ImportApplicationType.Types.SANCTION_ADHOC

        task = application.tasks.get()
        assert task.task_type == Task.TaskType.PREPARE
        assert task.is_active is True

    def test_anonymous_post_access_redirects(self):
        response = self.anonymous_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

    def test_forbidden_post_access(self):
        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestSanctionsAndAdhocImportAppplicationApplicantDetails(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.process = SanctionsAndAdhocLicenseApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.importer_user,
            last_updated_by=self.importer_user,
        )

        Task.objects.create(process=self.process, task_type=Task.TaskType.PREPARE)
        self.url = f"/import/sanctions/{self.process.pk}/edit/"
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
        assert self.importer.eori_number in response.content.decode()

    def test_save_application_details(self):
        app_ref = "REF64563343"
        exporter_name = "Exporter Name"
        exporter_address = "Exporter Address"

        data = {
            "contact": self.importer_user.pk,
            "applicant_reference": app_ref,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "exporter_name": exporter_name,
            "exporter_address": exporter_address,
        }
        self.importer_client.post(
            reverse("import:sanctions:edit", kwargs={"application_pk": self.process.pk}),
            data=data,
        )

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        application = SanctionsAndAdhocApplication.objects.get(pk=self.process.pk)
        assert application.contact == self.importer_user
        assert application.applicant_reference == app_ref
        assert application.origin_country == self.valid_country
        assert application.consignment_country == self.valid_country
        assert application.exporter_name == exporter_name
        assert application.exporter_address == exporter_address


class TestSanctionsGoodsDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, sanctions_app_in_progress):
        self.url = reverse(
            "import:sanctions:list-goods", kwargs={"application_pk": sanctions_app_in_progress.pk}
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

        assertTemplateUsed(response, "web/domains/case/import/sanctions/goods-list.html")

        context = response.context
        assert len(context["goods_list"]) == 2

        html = response.content.decode("utf-8")
        assert "Sanctions and Adhoc Licence Application - Goods" in html
        assert "Add Goods" in html

    def test_no_goods_shown(self, sanctions_app_in_progress):
        sanctions_app_in_progress.sanctions_goods.all().delete()
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assertTemplateUsed(response, "web/domains/case/import/sanctions/goods-list.html")

        context = response.context
        assert len(context["goods_list"]) == 0

        html = response.content.decode("utf-8")
        assert "There are no goods attached" in html
        assert "Add Goods" in html


class TestSanctionsAndAdhocImportAppplicationAddEditGoods(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.process = SanctionsAndAdhocLicenseApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.importer_user,
            last_updated_by=self.importer_user,
            origin_country=Country.objects.get(name="Iran"),
        )
        Task.objects.create(process=self.process, task_type=Task.TaskType.PREPARE)

        self.valid_commodity = Commodity.objects.get(commodity_code="2709009000")
        self.goods = SanctionsAndAdhocApplicationGoodsFactory.create(
            commodity=self.valid_commodity,
            goods_description="old desc",
            quantity_amount=5,
            value=5,
            import_application=self.process,
        )

        # f"/import/sanctions/{self.process.pk}/add-goods/"
        self.add_url = reverse(
            "import:sanctions:add-goods", kwargs={"application_pk": self.process.pk}
        )
        self.edit_url = reverse(
            "import:sanctions:edit-goods",
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
        assert "Sanctions and Adhoc Licence Application" in page_contents
        assert "In Progress" in page_contents
        assert self.importer.name in page_contents
        assert self.importer.eori_number in page_contents

    def test_add_goods(self):
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 1

        data = {
            "commodity": self.valid_commodity.pk,
            "goods_description": "test desc",
            "quantity_amount": 5,
            "value": 5,
        }
        response = self.importer_client.post(
            reverse("import:sanctions:add-goods", kwargs={"application_pk": self.process.pk}),
            data=data,
        )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "import:sanctions:list-goods", kwargs={"application_pk": self.process.pk}
        )
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 2

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
        assert "Sanctions and Adhoc Licence Application" in page_contents
        assert "In Progress" in page_contents
        assert self.importer.name in page_contents
        assert self.importer.eori_number in page_contents

    def test_edit_goods(self):
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 1
        goods = SanctionsAndAdhocApplicationGoodsFactory.create(
            commodity=self.valid_commodity,
            goods_description="old desc",
            quantity_amount=5,
            value=5,
            import_application=self.process,
        )
        data = {
            "commodity": self.valid_commodity.pk,
            "goods_description": "updated desc",
            "quantity_amount": 10,
            "value": 10,
        }
        response = self.importer_client.post(
            reverse(
                "import:sanctions:edit-goods",
                kwargs={"application_pk": self.process.pk, "goods_pk": goods.pk},
            ),
            data=data,
        )

        assert response.status_code == HTTPStatus.FOUND

        assert response.url == reverse(
            "import:sanctions:list-goods", kwargs={"application_pk": self.process.pk}
        )
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 2

        good = SanctionsAndAdhocApplicationGoods.objects.latest("pk")
        assert good.commodity == self.valid_commodity
        assert good.goods_description == "updated desc"
        assert good.quantity_amount == 10
        assert good.value == 10

    def test_delete_goods(self):
        goods = SanctionsAndAdhocApplicationGoods.objects.create(
            commodity=self.valid_commodity,
            goods_description="desc",
            quantity_amount=5,
            value=5,
            import_application=self.process,
        )
        assert len(SanctionsAndAdhocApplicationGoods.objects.all()) == 2
        data = {"action": "delete", "item": goods.pk}
        response = self.importer_client.post(
            reverse(
                "import:sanctions:delete-goods",
                kwargs={"application_pk": self.process.pk, "goods_pk": goods.pk},
            ),
            data=data,
        )
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "import:sanctions:list-goods", kwargs={"application_pk": self.process.pk}
        )
        assert len(SanctionsAndAdhocApplicationGoods.objects.all()) == 1


class TestSanctionsSupportingDocumentsDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, sanctions_app_in_progress):
        self.url = reverse(
            "import:sanctions:list-documents",
            kwargs={"application_pk": sanctions_app_in_progress.pk},
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
            response, "web/domains/case/import/sanctions/supporting-documents-list.html"
        )

        context = response.context
        assert len(context["supporting_documents"]) == 1

        html = response.content.decode("utf-8")
        assert "Sanctions and Adhoc Licence Application - Supporting Documents" in html
        assert "Add Supporting Document" in html

    def test_no_goods_shown(self, sanctions_app_in_progress):
        sanctions_app_in_progress.supporting_documents.all().delete()
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assertTemplateUsed(
            response, "web/domains/case/import/sanctions/supporting-documents-list.html"
        )

        context = response.context
        assert len(context["supporting_documents"]) == 0

        html = response.content.decode("utf-8")
        assert "There are no supporting documents attached" in html
        assert "Add Supporting Document" in html


class TestSubmitSanctions:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, sanctions_app_in_progress):
        self.app = sanctions_app_in_progress
        self.client = importer_client
        self.url = reverse(
            "import:sanctions:submit-sanctions", kwargs={"application_pk": self.app.pk}
        )

    def test_submit_catches_duplicate_commodities(self):
        sanction_usage = get_usage_records(ImportApplicationType.Types.SANCTION_ADHOC).filter(
            country=self.app.origin_country
        )
        available_commodities = get_usage_commodities(sanction_usage)
        commodity = available_commodities.first()
        another_commodity = available_commodities.last()

        self.app.sanctions_goods.all().delete()
        self.app.sanctions_goods.create(
            commodity=commodity, goods_description="Goods 1", quantity_amount=1, value=1
        )

        self.app.sanctions_goods.create(
            commodity=commodity, goods_description="Goods 2 (dupe)", quantity_amount=1, value=1
        )

        self.app.sanctions_goods.create(
            commodity=another_commodity, goods_description="Goods 3", quantity_amount=1, value=1
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
        # All countries available in the sanctions form
        available_countries = Country.app.get_sanctions_coo_and_coc_countries()
        # Countries with sanctions
        sanctioned_countries = Country.app.get_sanctions_countries()

        # set a valid non-sanctioned country for origin
        self.app.origin_country = available_countries.difference(sanctioned_countries).first()
        self.app.consignment_country = sanctioned_countries.first()

        sanction_usage = get_usage_records(ImportApplicationType.Types.SANCTION_ADHOC).filter(
            country=self.app.consignment_country
        )
        available_commodities = get_usage_commodities(sanction_usage)

        commodity = Commodity.objects.all().difference(available_commodities).first()

        self.app.sanctions_goods.all().delete()
        # Add an invalid commodity
        self.app.sanctions_goods.create(
            commodity=commodity, goods_description="Goods 1", quantity_amount=1, value=1
        )

        response = self.client.get(self.url)

        errors: ApplicationErrors = response.context["errors"]
        check_page_errors(errors, "Application Details", ["Goods - Commodity Code"])

        page_errors: PageErrors = errors.get_page_errors("Application Details")
        assert page_errors.errors[0].field_name == "Goods - Commodity Code"
        assert page_errors.errors[0].messages == [
            f"Commodity '{commodity.commodity_code}' is invalid for the selected country of manufacture or country of shipment."
        ]
