from django.test import TestCase
from web.domains.legislation.models import ProductLegislation


class ProductLegislationTest(TestCase):
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
        self.assertTrue(isinstance(product_legisation, ProductLegislation))
        self.assertEqual(product_legisation.name, "Test Legislation")
        self.assertFalse(product_legisation.is_biocidal)
        self.assertFalse(product_legisation.is_biocidal_claim)
        self.assertTrue(product_legisation.is_eu_cosmetics_regulation)

    def test_archive_legislation(self):
        product_legisation = self.create_legislation()
        product_legisation.archive()
        self.assertFalse(product_legisation.is_active)

    def test_unarchive_legislation(self):
        product_legisation = self.create_legislation()
        product_legisation.unarchive()
        self.assertTrue(product_legisation.is_active)

    def test_biocidal_yes_no_label(self):
        product_legisation = self.create_legislation()
        self.assertEqual(product_legisation.is_biocidal_yes_no, "No")
        product_legisation.is_biocidal = True
        self.assertEqual(product_legisation.is_biocidal_yes_no, "Yes")

    def test_biocidal_claim_yes_no_label(self):
        product_legisation = self.create_legislation()
        product_legisation.is_biocidal_claim = True
        self.assertEqual(product_legisation.is_biocidal_claim_yes_no, "Yes")

    def test_cosmetics_regulation_yes_no_label(self):
        product_legisation = self.create_legislation()
        self.assertEqual(product_legisation.is_eu_cosmetics_regulation_yes_no, "Yes")

    def test_string_representation(self):
        product_legisation = self.create_legislation()
        self.assertEqual(
            product_legisation.__str__(), f"Product Legislation ({product_legisation.name})"
        )
