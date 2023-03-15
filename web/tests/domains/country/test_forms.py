from django.test import TestCase

from web.domains.country.forms import (
    CountryCreateForm,
    CountryEditForm,
    CountryGroupEditForm,
    CountryNameFilter,
    CountryTranslationEditForm,
    CountryTranslationSetEditForm,
)
from web.models import Country

from .factory import (
    CountryFactory,
    CountryGroupFactory,
    CountryTranslationFactory,
    CountryTranslationSetFactory,
)


class CountryNameFilterTest(TestCase):
    def setUp(self):
        CountryFactory(name="Gondor", is_active=True)
        CountryFactory(name="Mordor", is_active=True)
        CountryFactory(name="Rohan", is_active=False)
        CountryFactory(name="Shire", is_active=False)

    def run_filter(self, data=None):
        return CountryNameFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({"country_name": "dor"})
        self.assertEqual(results.count(), 4)

    def test_filter_finds_active_only(self):
        results = self.run_filter({"country_name": "o"})
        self.assertEqual(results.count(), 63)
        self.assertTrue(results.first().is_active)
        self.assertTrue(results.last().is_active)


class CountryCreateFormTest(TestCase):
    def test_form_valid(self):
        form = CountryCreateForm(
            data={
                "name": "Italy",
                "type": Country.SOVEREIGN_TERRITORY,
                "commission_code": "TEST",
                "hmrc_code": "TST",
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = CountryCreateForm(data={})
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = CountryCreateForm(
            data={"name": "Japan", "type": Country.SYSTEM, "commission_code": "TEST"}
        )
        self.assertEqual(len(form.errors), 1)
        message = form.errors["hmrc_code"][0]
        self.assertEqual(message, "You must enter this item")


class CountryEditFormTest(TestCase):
    def test_form_valid(self):
        form = CountryEditForm(
            instance=CountryFactory(),
            data={"name": "Taiwan", "commission_code": "TEST", "hmrc_code": "TST"},
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = CountryEditForm(instance=CountryFactory(), data={})
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = CountryEditForm(
            instance=CountryFactory(),
            data={"name": "", "commission_code": "TEST", "hmrc_code": "TST"},
        )
        self.assertEqual(len(form.errors), 1)
        message = form.errors["name"][0]
        self.assertEqual(message, "You must enter this item")


class CountryGroupEditFormTest(TestCase):
    def test_form_valid(self):
        form = CountryGroupEditForm(instance=CountryGroupFactory(), data={"name": "Some countries"})
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = CountryGroupEditForm(instance=CountryGroupFactory(), data={})
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = CountryGroupEditForm(instance=CountryGroupFactory(), data={})
        self.assertEqual(len(form.errors), 1)
        message = form.errors["name"][0]
        self.assertEqual(message, "You must enter this item")


class CountryTranslationSetEditFormTest(TestCase):
    def test_form_valid(self):
        form = CountryTranslationSetEditForm(
            instance=CountryTranslationSetFactory(), data={"name": "Dothraki"}
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = CountryTranslationSetEditForm(data={})
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = CountryTranslationSetEditForm(data={})
        self.assertEqual(len(form.errors), 1)
        message = form.errors["name"][0]
        self.assertEqual(message, "You must enter this item")


class CountryTranslationEditFormTest(TestCase):
    def test_form_valid(self):
        form = CountryTranslationEditForm(
            instance=CountryTranslationFactory(), data={"translation": "İtalya"}
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = CountryTranslationEditForm(data={})
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = CountryTranslationEditForm(data={})
        self.assertEqual(len(form.errors), 1)
        message = form.errors["translation"][0]
        self.assertEqual(message, "You must enter this item")
