from django.test import TestCase
from web.domains.country.models import (
    Country,
    CountryGroup,
    CountryTranslation,
    CountryTranslationSet,
)

from .factory import CountryFactory, CountryTranslationSetFactory


class CountryTest(TestCase):
    def create_country(self, name="Test Country", is_active=True, type=Country.SOVEREIGN_TERRITORY):
        return Country.objects.create(name=name, is_active=is_active, type=type)

    def test_create_country(self):
        country = self.create_country()
        self.assertTrue(isinstance(country, Country))
        self.assertEqual(country.name, "Test Country")
        self.assertTrue(country.is_active)

    def test_name_slug(self):
        country = self.create_country(name="Papua Awesome Guinea")
        self.assertEqual(country.name_slug, "papua_awesome_guinea")

    def test_string_representation(self):
        country = self.create_country()
        self.assertEqual(country.__str__(), f"Country ({country.name})")


class CountryGroupTest(TestCase):
    def create_country_group(self, name="Test Group", comments=None):
        return CountryGroup.objects.create(name=name, comments=comments)

    def test_create_country_group(self):
        group = self.create_country_group(name="Some Countries", comments="testing")
        self.assertTrue(isinstance(group, CountryGroup))
        self.assertEqual(group.name, "Some Countries")

    def test_string_representation(self):
        group = self.create_country_group(name="EU Countries")
        self.assertEqual(group.__str__(), "Country Group (EU Countries)")


class CountryTranslationSetTest(TestCase):
    def create_translation_set(self, name="French", is_active=True):
        return CountryTranslationSet.objects.create(name=name, is_active=is_active)

    def test_create_translation_set(self):
        set = self.create_translation_set(is_active=False)
        self.assertTrue(isinstance(set, CountryTranslationSet))
        self.assertEqual(set.name, "French")
        self.assertFalse(set.is_active)

    def test_archive_translation_set(self):
        set = self.create_translation_set(is_active=True)
        set.archive()
        self.assertFalse(set.is_active)

    def test_unarchive_translation_set(self):
        set = self.create_translation_set(is_active=False)
        set.unarchive()
        self.assertTrue(set.is_active)

    def test_string_representation(self):
        translation_set = self.create_translation_set(name="Sindarin")
        self.assertEqual(translation_set.__str__(), "Country Translation Set (Sindarin)")


class CountryTranslationTest(TestCase):
    def create_translation(translation="Finlande"):
        return CountryTranslation.objects.create(
            translation=translation,
            country=CountryFactory(),
            translation_set=CountryTranslationSetFactory(),
        )
