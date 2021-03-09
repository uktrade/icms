from guardian.shortcuts import assign_perm

from web.domains.case._import.sanctions.forms import (
    GoodsForm,
    SanctionsAndAdhocLicenseForm,
)
from web.domains.country.models import Country
from web.domains.importer.models import Importer
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import (
    SanctionsAndAdhocLicenseApplicationFactory,
)
from web.tests.domains.commodity.factory import CommodityFactory, CommodityTypeFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.flow.factories import TaskFactory


class SanctionsAndAdhocImportAppplicationFormTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        Country.objects.filter(country_groups__name="Sanctions and Adhoc License")

        self.valid_country = Country.objects.filter(
            country_groups__name="Sanctions and Adhoc License"
        ).first()
        self.invalid_country = Country.objects.exclude(
            country_groups__name="Sanctions and Adhoc License"
        ).first()

        self.importer = ImporterFactory.create(
            type=Importer.ORGANISATION,
            user=self.user,
            name="Importer Limited",
            eori_number="GB3423453234",
        )
        self.process = SanctionsAndAdhocLicenseApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.user,
            last_updated_by=self.user,
        )
        TaskFactory.create(process=self.process, task_type="prepare")

        assign_perm("web.is_contact_of_importer", self.user, self.importer)
        self.login_with_permissions(["importer_access"])

    def test_sa_form_valid(self):
        data = {
            "contact": self.user.pk,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "exporter_name": None,
            "exporter_address": None,
        }
        form = SanctionsAndAdhocLicenseForm(
            data, instance=self.process, initial={"contact": self.user}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_sa_form_invalid_with_wrong_country(self):
        data = {
            "contact": self.user.pk,
            "origin_country": self.invalid_country.pk,
            "consignment_country": self.invalid_country.pk,
            "exporter_name": None,
            "exporter_address": None,
        }
        form = SanctionsAndAdhocLicenseForm(
            data, instance=self.process, initial={"contact": self.user}
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

    def test_sa_form_invalid_without_required_fields(self):
        data = {"exporter_name": None, "exporter_address": None}
        form = SanctionsAndAdhocLicenseForm(
            data, instance=self.process, initial={"contact": self.user}
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertEqual(len(form.errors), 3)

    def test_goods_form_valid(self):
        commodity_type = CommodityTypeFactory.create()
        commodity = CommodityFactory.create(commodity_type=commodity_type)

        data = {
            "commodity_code": commodity.pk,
            "goods_description": "test desc",
            "quantity_amount": 5,
            "value": 5,
        }
        form = GoodsForm(data)
        self.assertTrue(form.is_valid())

    def test_goods_form_invalid(self):
        data = {}
        form = GoodsForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)
