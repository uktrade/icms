from django.test import TestCase

from web.domains.legislation.forms import (
    ProductLegislationFilter,
    ProductLegislationForm,
)


class TestProductLegislationFilter(TestCase):

    def run_filter(self, data=None):
        return ProductLegislationFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({"name": "aerosol"})
        assert results.count() == 3

    def test_biocidal_filter(self):
        results = self.run_filter({"is_biocidal": False})
        assert results.count() == 92

    def test_biocidal_claim_filter(self):
        results = self.run_filter({"is_biocidal_claim": True})
        assert results.count() == 1

        first = results.get()
        assert first.name == "Dummy 'Is Biocidal Claim legislation'"

    def test_is_cosmetics_regulation_filter(self):
        results = self.run_filter({"is_eu_cosmetics_regulation": True})
        assert results.count() == 3

    def test_status_filter(self):
        results = self.run_filter({"status": True})
        assert results.count() == 60

    def test_filter_order(self):
        results = self.run_filter({"name": "The EC"})
        assert results.count() == 3
        first = results.first()
        last = results.last()
        assert first.name == "The EC Fertilisers (England and Wales) Regulations 2006"
        assert last.name == "The EC Fertilisers (Scotland) Regulations 2006"

    def test_status_initial(self):
        filter = ProductLegislationFilter()
        assert filter.form.fields["status"].initial is True


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
