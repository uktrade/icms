import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import (
    Commodity,
    Country,
    ImportApplicationType,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
    Task,
)
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import (
    SanctionsAndAdhocApplicationGoodsFactory,
    SanctionsAndAdhocLicenseApplicationFactory,
)

LOGIN_URL = "/"


class TestSanctionsAndAdhocImportAppplicationCreateView(AuthTestCase):
    url = "/import/create/sanctions/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_create_ok(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 200

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
        assert response.status_code == 302

    def test_forbidden_post_access(self):
        response = self.exporter_client.post(self.url)
        assert response.status_code == 403


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

        self.valid_country = Country.objects.filter(
            country_groups__name="Sanctions and Adhoc License"
        ).first()

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)

        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_logged_in_permissions(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 200

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
        assert response.status_code == 200
        application = SanctionsAndAdhocApplication.objects.get(pk=self.process.pk)
        assert application.contact == self.importer_user
        assert application.applicant_reference == app_ref
        assert application.origin_country == self.valid_country
        assert application.consignment_country == self.valid_country
        assert application.exporter_name == exporter_name
        assert application.exporter_address == exporter_address
        assert "There are no goods attached" in response.content.decode()


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

        assert response.status_code == 302
        assertRedirects(response, self.add_redirect_url)

    def test_add_forbidden_access(self):
        response = self.exporter_client.get(self.add_url)
        assert response.status_code == 403

    def test_add_logged_in_permissions(self):
        response = self.importer_client.get(self.add_url)
        assert response.status_code == 200

    def test_add_page_content(self):
        response = self.importer_client.get(self.add_url)
        assert response.status_code == 200
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
        assert response.status_code == 302
        assert response.url == reverse(
            "import:sanctions:edit", kwargs={"application_pk": self.process.pk}
        )
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 2

    def test_edit_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.edit_url)

        assert response.status_code == 302
        assertRedirects(response, self.edit_redirect_url)

    def test_edit_forbidden_access(self):
        response = self.exporter_client.get(self.edit_url)
        assert response.status_code == 403

    def test_edit_logged_in_permissions(self):
        response = self.importer_client.get(self.edit_url)
        assert response.status_code == 200

    def test_edit_page_content(self):
        response = self.importer_client.get(self.edit_url)
        assert response.status_code == 200
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

        assert response.status_code == 302

        assert response.url == reverse(
            "import:sanctions:edit", kwargs={"application_pk": self.process.pk}
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
        assert response.status_code == 302
        assert response.url == reverse(
            "import:sanctions:edit", kwargs={"application_pk": self.process.pk}
        )
        assert len(SanctionsAndAdhocApplicationGoods.objects.all()) == 1
