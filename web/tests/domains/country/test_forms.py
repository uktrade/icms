from django.test import TestCase

from web.domains.country.forms import (
    CountryCreateForm,
    CountryEditForm,
    CountryGroupEditForm,
    CountryNameFilter,
    CountryTranslationEditForm,
    CountryTranslationSetEditForm,
)
from web.domains.country.types import CountryGroupName
from web.models import Country, CountryGroup

from .factory import (
    CountryFactory,
    CountryTranslationFactory,
    CountryTranslationSetFactory,
)


class TestCountryNameFilter(TestCase):
    def setUp(self):
        CountryFactory(name="Gondor", is_active=True)
        CountryFactory(name="Mordor", is_active=True)
        CountryFactory(name="Rohan", is_active=False)
        CountryFactory(name="Shire", is_active=False)

    def run_filter(self, data=None):
        return CountryNameFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({"country_name": "dor"})
        assert results.count() == 4

    def test_filter_finds_active_only(self):
        results = self.run_filter({"country_name": "o"})
        assert results.count() == 67
        assert results.first().is_active is True
        assert results.last().is_active is True


class TestCountryCreateForm(TestCase):
    def setUp(self):
        self.AFGHANISTAN = Country.objects.get(pk=1)
        self.CHAD = Country.objects.get(pk=200)

    def test_form_valid(self):

        form = CountryCreateForm(
            data={
                "name": self.CHAD.pk,
            }
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = CountryCreateForm(data={})
        assert form.is_valid() is False, form.errors

    def test_invalid_form_message(self):
        form = CountryCreateForm(data={"name": self.AFGHANISTAN.pk})
        assert len(form.errors) == 1
        message = form.errors["name"][0]
        assert message == "Select a valid choice. That choice is not one of the available choices."


class TestCountryEditForm(TestCase):
    def setUp(self):
        self.AFGHANISTAN = Country.objects.get(pk=1)

    def test_form_valid(self):
        form = CountryEditForm(
            instance=self.AFGHANISTAN,
            data={"name": "A"},
        )
        assert form.is_valid() is True

    def test_form_invalid(self):

        form = CountryEditForm(instance=self.AFGHANISTAN, data={})
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = CountryEditForm(
            instance=self.AFGHANISTAN,
            data={"name": ""},
        )
        assert len(form.errors) == 1
        message = form.errors["name"][0]
        assert message == "You must enter this item"


class TestCountryGroupEditForm(TestCase):
    def test_form_valid(self):
        group = CountryGroup.objects.get(name=CountryGroupName.EU)
        form = CountryGroupEditForm(instance=group, data={"comments": "A test comment"})
        assert form.is_valid() is True


class TestCountryTranslationSetEditForm(TestCase):
    def test_form_valid(self):
        form = CountryTranslationSetEditForm(
            instance=CountryTranslationSetFactory(), data={"name": "Dothraki"}
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = CountryTranslationSetEditForm(data={})
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = CountryTranslationSetEditForm(data={})
        assert len(form.errors) == 1
        message = form.errors["name"][0]
        assert message == "You must enter this item"


class TestCountryTranslationEditForm(TestCase):
    def test_form_valid(self):
        form = CountryTranslationEditForm(
            instance=CountryTranslationFactory(), data={"translation": "İtalya"}
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = CountryTranslationEditForm(data={})
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = CountryTranslationEditForm(data={})
        assert len(form.errors) == 1
        message = form.errors["translation"][0]
        assert message == "You must enter this item"
