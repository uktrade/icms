from django.urls import reverse
from guardian.shortcuts import assign_perm

from web.domains.case._import.models import ImportApplicationType
from web.domains.case._import.sanctions.models import (
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
)
from web.domains.country.models import Country
from web.domains.importer.models import Importer
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import (
    SanctionsAndAdhocApplicationGoodsFactory,
    SanctionsAndAdhocLicenseApplicationFactory,
)
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory
from web.tests.flow.factories import TaskFactory

LOGIN_URL = "/"


class SanctionsAndAdhocImportAppplicationCreateViewTest(AuthTestCase):
    url = "/import/create/sanctions/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_create_ok(self):
        office = OfficeFactory.create(is_active=True)
        importer = ImporterFactory.create(is_active=True, offices=[office])

        assign_perm("web.is_contact_of_importer", self.user, importer)
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.post(
            reverse("import:create-sanctions"),
            data={"importer": importer.pk, "importer_office": office.pk},
        )
        application = SanctionsAndAdhocApplication.objects.get()
        self.assertEqual(application.process_type, SanctionsAndAdhocApplication.PROCESS_TYPE)

        application_type = application.application_type
        self.assertEqual(application_type.type, ImportApplicationType.Types.SANCTION_ADHOC)

        task = application.tasks.get()
        self.assertEqual(task.task_type, "prepare")
        self.assertEqual(task.is_active, True)

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


class SanctionsAndAdhocImportAppplicationApplicantDetailsTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer_name = "Importer Limited"
        self.importer_eori = "GB3423453234"

        self.importer = ImporterFactory.create(
            type=Importer.ORGANISATION,
            user=self.user,
            name=self.importer_name,
            eori_number=self.importer_eori,
        )

        self.process = SanctionsAndAdhocLicenseApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.user,
            last_updated_by=self.user,
        )

        TaskFactory.create(process=self.process, task_type="prepare")
        self.url = f"/import/sanctions/{self.process.pk}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

        self.valid_country = Country.objects.filter(
            country_groups__name="Sanctions and Adhoc License"
        ).first()

        assign_perm("web.is_contact_of_importer", self.user, self.importer)

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_logged_in_permissions(self):
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_page_content(self):
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.url)
        assert self.importer_name in response.content.decode()
        assert self.importer_eori in response.content.decode()

    def test_save_application_details(self):
        self.login_with_permissions(["importer_access"])

        app_ref = "REF64563343"
        exporter_name = "Exporter Name"
        exporter_address = "Exporter Address"

        data = {
            "contact": self.user.pk,
            "applicant_reference": app_ref,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "exporter_name": exporter_name,
            "exporter_address": exporter_address,
        }
        self.client.post(
            reverse("import:sanctions:edit-application", kwargs={"pk": self.process.pk}),
            data=data,
        )

        response = self.client.get(self.url)
        assert response.status_code == 200
        application = SanctionsAndAdhocApplication.objects.get(pk=self.process.pk)
        assert application.contact == self.user
        assert application.applicant_reference == app_ref
        assert application.origin_country == self.valid_country
        assert application.consignment_country == self.valid_country
        assert application.exporter_name == exporter_name
        assert application.exporter_address == exporter_address
        assert "There are no goods attached" in response.content.decode()


class SanctionsAndAdhocImportAppplicationAddEditGoods(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer_name = "Importer Limited"
        self.importer_eori = "GB3423453234"

        self.importer = ImporterFactory.create(
            type=Importer.ORGANISATION,
            user=self.user,
            name=self.importer_name,
            eori_number=self.importer_eori,
        )

        self.process = SanctionsAndAdhocLicenseApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.user,
            last_updated_by=self.user,
        )
        TaskFactory.create(process=self.process, task_type="prepare")

        self.goods = SanctionsAndAdhocApplicationGoodsFactory.create(
            commodity_code="2850009000",
            goods_description="old desc",
            quantity_amount=5,
            value=5,
            import_application=self.process,
        )

        self.add_url = f"/import/sanctions/{self.process.pk}/add-goods/"
        self.edit_url = f"/import/sanctions/{self.process.pk}/goods/{self.goods.pk}/edit/"
        self.add_redirect_url = f"{LOGIN_URL}?next={self.add_url}"
        self.edit_redirect_url = f"{LOGIN_URL}?next={self.edit_url}"

        assign_perm("web.is_contact_of_importer", self.user, self.importer)

    def test_add_anonymous_access_redirects(self):
        response = self.client.get(self.add_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.add_redirect_url)

    def test_add_forbidden_access(self):
        self.login()

        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_logged_in_permissions(self):
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.add_url)
        assert response.status_code == 200

    def test_add_page_content(self):
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.add_url)
        assert response.status_code == 200
        page_contents = response.content.decode()

        # Header
        assert "Sanctions and Adhoc - SAN_TEMP" in page_contents
        assert "In Progress" in page_contents
        assert self.importer_name in page_contents
        assert self.importer_eori in page_contents

    def test_add_goods(self):
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 1
        self.login_with_permissions(["importer_access"])

        data = {
            "commodity_code": "2850009000",
            "goods_description": "test desc",
            "quantity_amount": 5,
            "value": 5,
        }
        response = self.client.post(
            reverse("import:sanctions:add-goods", kwargs={"pk": self.process.pk}),
            data=data,
        )
        assert response.status_code == 302
        assert response.url == reverse(
            "import:sanctions:edit-application", kwargs={"pk": self.process.pk}
        )
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 2

    def test_edit_anonymous_access_redirects(self):
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.edit_redirect_url)

    def test_edit_forbidden_access(self):
        self.login()

        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_logged_in_permissions(self):
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.edit_url)
        assert response.status_code == 200

    def test_edit_page_content(self):
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.edit_url)
        assert response.status_code == 200
        page_contents = response.content.decode()

        # Header
        assert "Sanctions and Adhoc - SAN_TEMP" in page_contents
        assert "In Progress" in page_contents
        assert self.importer_name in page_contents
        assert self.importer_eori in page_contents

    def test_edit_goods(self):
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 1
        self.login_with_permissions(["importer_access"])

        goods = SanctionsAndAdhocApplicationGoodsFactory.create(
            commodity_code="2850009000",
            goods_description="old desc",
            quantity_amount=5,
            value=5,
            import_application=self.process,
        )
        data = {
            "commodity_code": "2850002070",
            "goods_description": "updated desc",
            "quantity_amount": 10,
            "value": 10,
        }
        response = self.client.post(
            reverse(
                "import:sanctions:edit-goods",
                kwargs={"application_pk": self.process.pk, "goods_pk": goods.pk},
            ),
            data=data,
        )

        assert response.status_code == 302

        assert response.url == reverse(
            "import:sanctions:edit-application", kwargs={"pk": self.process.pk}
        )
        assert SanctionsAndAdhocApplicationGoods.objects.count() == 2

        good = SanctionsAndAdhocApplicationGoods.objects.latest("pk")
        assert good.commodity_code == "2850002070"
        assert good.goods_description == "updated desc"
        assert good.quantity_amount == 10
        assert good.value == 10

    def test_delete_goods(self):
        self.login_with_permissions(["importer_access"])
        goods = SanctionsAndAdhocApplicationGoods.objects.create(
            commodity_code="2850002070",
            goods_description="desc",
            quantity_amount=5,
            value=5,
            import_application=self.process,
        )
        assert len(SanctionsAndAdhocApplicationGoods.objects.all()) == 2
        data = {"action": "delete", "item": goods.pk}
        response = self.client.post(
            reverse(
                "import:sanctions:delete-goods",
                kwargs={"application_pk": self.process.pk, "goods_pk": goods.pk},
            ),
            data=data,
        )
        assert response.status_code == 302
        assert response.url == reverse(
            "import:sanctions:edit-application", kwargs={"pk": self.process.pk}
        )
        assert len(SanctionsAndAdhocApplicationGoods.objects.all()) == 1
