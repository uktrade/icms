from django.test import TestCase

from web.domains.legislation.forms import (
    ProductLegislationFilter,
    ProductLegislationForm,
)

from .factory import ProductLegislationFactory


class TestProductLegislationFilter(TestCase):
    def setUp(self):
        """Supplementary data to data already added in migrations"""

        ProductLegislationFactory(
            name="Test Legislation",
            is_biocidal=True,
            is_biocidal_claim=True,
            is_eu_cosmetics_regulation=True,
            is_active=False,
        )
        ProductLegislationFactory(
            name="Comprehensive legislation",
            is_biocidal=False,
            is_biocidal_claim=False,
            is_eu_cosmetics_regulation=True,
            is_active=True,
        )
        ProductLegislationFactory(
            name="New Product Legislation",
            is_biocidal=True,
            is_biocidal_claim=False,
            is_eu_cosmetics_regulation=False,
            is_active=False,
        )
        ProductLegislationFactory(
            name="Eu Test Cosmetics Regulation",
            is_biocidal=True,
            is_biocidal_claim=False,
            is_eu_cosmetics_regulation=False,
            is_active=False,
        )

    def run_filter(self, data=None):
        return ProductLegislationFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({"name": "legislation"})
        assert results.count() == 3

    def test_biocidal_filter(self):
        results = self.run_filter({"is_biocidal": False})
        assert results.count() == 25

    def test_biocidal_claim_filter(self):
        results = self.run_filter({"is_biocidal_claim": True})
        assert results.count() == 3

        # Check the test legislation is in the results
        results = results.filter(name="Test Legislation")
        first = results.first()
        assert first.name == "Test Legislation"

    def test_is_cosmetics_regulation_filter(self):
        results = self.run_filter({"is_eu_cosmetics_regulation": True})
        assert results.count() == 2

    def test_status_filter(self):
        results = self.run_filter({"status": True})
        assert results.count() == 27

    def test_filter_order(self):
        results = self.run_filter({"name": "legislation"})
        assert results.count() == 3
        first = results.first()
        last = results.last()
        assert first.name == "Comprehensive legislation"
        assert last.name == "Test Legislation"


class TestProductLegislationForm(TestCase):
    def test_form_valid(self):
        form = ProductLegislationForm(data={"name": "Testing"})
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = ProductLegislationForm(data={})
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = ProductLegislationForm(data={})
        assert len(form.errors) == 1
        message = form.errors["name"][0]
        assert message == "You must enter this item"
