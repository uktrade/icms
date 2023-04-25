from django.test import TestCase

from web.models import Country, CountryGroup, CountryTranslation, CountryTranslationSet

from .factory import CountryFactory, CountryTranslationSetFactory


class TestCountry(TestCase):
    def create_country(self, name="Test Country", is_active=True, type=Country.SOVEREIGN_TERRITORY):
        return Country.objects.create(name=name, is_active=is_active, type=type)

    def test_create_country(self):
        country = self.create_country()
        assert isinstance(country, Country)
        assert country.name == "Test Country"
        assert country.is_active is True

    def test_name_slug(self):
        country = self.create_country(name="Papua Awesome Guinea")
        assert country.name_slug == "papua_awesome_guinea"

    def test_string_representation(self):
        country = self.create_country()
        assert country.__str__() == f"{country.name}"


class TestCountryGroup(TestCase):
    def create_country_group(self, name="Test Group", comments=None):
        return CountryGroup.objects.create(name=name, comments=comments)

    def test_create_country_group(self):
        group = self.create_country_group(name="Some Countries", comments="testing")
        assert isinstance(group, CountryGroup)
        assert group.name == "Some Countries"

    def test_string_representation(self):
        group = self.create_country_group(name="EU Countries")
        country = TestCountry().create_country()
        group.countries.add(country)
        group.save()
        assert group.__str__() == "EU Countries - (1 countries)"


class TestCountryTranslationSet(TestCase):
    def create_translation_set(self, name="French", is_active=True):
        return CountryTranslationSet.objects.create(name=name, is_active=is_active)

    def test_create_translation_set(self):
        set = self.create_translation_set(is_active=False)
        assert isinstance(set, CountryTranslationSet)
        assert set.name == "French"
        assert set.is_active is False

    def test_archive_translation_set(self):
        set = self.create_translation_set(is_active=True)
        set.archive()
        assert set.is_active is False

    def test_unarchive_translation_set(self):
        set = self.create_translation_set(is_active=False)
        set.unarchive()
        assert set.is_active is True

    def test_string_representation(self):
        translation_set = self.create_translation_set(name="Sindarin")
        assert translation_set.__str__() == "Country Translation Set (Sindarin)"


class TestCountryTranslation(TestCase):
    def create_translation(translation="Finlande"):
        return CountryTranslation.objects.create(
            translation=translation,
            country=CountryFactory(),
            translation_set=CountryTranslationSetFactory(),
        )
