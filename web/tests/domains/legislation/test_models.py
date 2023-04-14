from django.test import TestCase

from web.models import ProductLegislation


class TestProductLegislation(TestCase):
    def create_legislation(
        self,
        name="Test Legislation",
        is_active=True,
        is_biocidal=False,
        is_eu_cosmetics_regulation=True,
        is_biocidal_claim=False,
    ):
        return ProductLegislation.objects.create(
            name=name,
            is_active=is_active,
            is_biocidal=is_biocidal,
            is_eu_cosmetics_regulation=is_eu_cosmetics_regulation,
            is_biocidal_claim=is_biocidal_claim,
        )

    def test_create_legislation(self):
        product_legisation = self.create_legislation()
        assert isinstance(product_legisation, ProductLegislation)
        assert product_legisation.name == "Test Legislation"
        assert product_legisation.is_biocidal is False
        assert product_legisation.is_biocidal_claim is False
        assert product_legisation.is_eu_cosmetics_regulation is True

    def test_archive_legislation(self):
        product_legisation = self.create_legislation()
        product_legisation.archive()
        assert product_legisation.is_active is False

    def test_unarchive_legislation(self):
        product_legisation = self.create_legislation()
        product_legisation.unarchive()
        assert product_legisation.is_active is True

    def test_biocidal_yes_no_label(self):
        product_legisation = self.create_legislation()
        assert product_legisation.is_biocidal_yes_no == "No"
        product_legisation.is_biocidal = True
        assert product_legisation.is_biocidal_yes_no == "Yes"

    def test_biocidal_claim_yes_no_label(self):
        product_legisation = self.create_legislation()
        product_legisation.is_biocidal_claim = True
        assert product_legisation.is_biocidal_claim_yes_no == "Yes"

    def test_cosmetics_regulation_yes_no_label(self):
        product_legisation = self.create_legislation()
        assert product_legisation.is_eu_cosmetics_regulation_yes_no == "Yes"

    def test_string_representation(self):
        product_legisation = self.create_legislation()
        assert product_legisation.__str__() == product_legisation.name
