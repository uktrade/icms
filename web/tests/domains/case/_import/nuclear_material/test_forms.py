import datetime as dt

import pytest

from web.domains.case._import.nuclear_material.forms import (
    GoodsForm,
    GoodsNuclearMaterialApplicationForm,
    SubmitNuclearMaterialApplicationForm,
    nuclear_material_available_units,
)
from web.forms.fields import JQUERY_DATE_FORMAT
from web.models import Commodity, Country, NuclearMaterialApplication
from web.tests.auth import AuthTestCase


class TestNuclearMaterialApplicationForms(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, nuclear_app_in_progress):
        self.valid_country = Country.util.get_all_countries().get(name="Iran")
        self.process = nuclear_app_in_progress
        self.goods = self.process.nuclear_goods.first()

    def test_nuclear_form_valid(self):
        data = {
            "contact": self.importer_user.pk,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "nature_of_business": "Test nature of business",
            "consignor_name": "Test consignor name",
            "consignor_address": "Test consignor address",
            "end_user_name": "Test end user name",
            "end_user_address": "Test end user address",
            "intended_use_of_shipment": "Test intended use of shipment",
            "shipment_start_date": dt.date.today().strftime(JQUERY_DATE_FORMAT),
            "shipment_end_date": "",
            "security_team_contact_information": "Test security team contact information",
            "licence_type": NuclearMaterialApplication.LicenceType.SINGLE,
        }
        form = SubmitNuclearMaterialApplicationForm(
            data, instance=self.process, initial={"contact": self.importer_user}
        )
        assert form.is_valid(), form.errors

    def test_nuclear_form_invalid_without_required_fields(self):
        data = {
            "contact": self.importer_user.pk,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "nature_of_business": None,
            "consignor_name": None,
            "consignor_address": None,
            "end_user_name": None,
            "end_user_address": None,
            "intended_use_of_shipment": None,
            "shipment_start_date": None,
            "shipment_end_date": None,
            "security_team_contact_information": None,
            "licence_type": None,
        }
        form = SubmitNuclearMaterialApplicationForm(
            data, instance=self.process, initial={"contact": self.importer_user}
        )
        assert form.is_valid() is False
        assert form.errors
        assert len(form.errors) == 9

    def test_goods_form_valid(self):
        data = {
            "commodity": Commodity.objects.get(commodity_code="2844101000").pk,
            "goods_description": "test desc",
            "quantity_amount": 5,
            "quantity_unit": nuclear_material_available_units().first().pk,
        }
        form = GoodsForm(data)
        assert form.is_valid() is True
        assert form.cleaned_data["goods_description"] == "test desc"

    def test_goods_form_invalid(self):
        data = {}
        form = GoodsForm(data)
        assert form.is_valid() is False
        assert len(form.errors) == 4

    def test_goods_form_description_cleaned(self):
        data = {
            "commodity": Commodity.objects.get(commodity_code="2844101000").pk,
            "goods_description": " some\r\n goods \t description\n  ",
            "quantity_amount": 5,
            "quantity_unit": nuclear_material_available_units().first().pk,
        }
        form = GoodsForm(data)
        assert form.is_valid() is True
        assert form.cleaned_data["goods_description"] == "some goods description"

    def test_goods_sanction_licence_form(self):
        data = {
            "goods_description": "some goods description",
            "quantity_amount": 5,
            "quantity_unit": nuclear_material_available_units().first().pk,
        }
        form = GoodsNuclearMaterialApplicationForm(data=data, instance=self.goods)
        assert form.is_valid() is True
        assert form.cleaned_data["goods_description"] == "some goods description"

    def test_goods_sanction_licence_form_description_cleaned(self):
        data = {
            "goods_description": " some\r\n goods \t description\n  ",
            "quantity_amount": 5,
            "quantity_unit": nuclear_material_available_units().first().pk,
        }
        form = GoodsNuclearMaterialApplicationForm(data=data, instance=self.goods)
        assert form.is_valid() is True
        assert form.cleaned_data["goods_description"] == "some goods description"
