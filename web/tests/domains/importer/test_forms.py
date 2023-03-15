from unittest.mock import patch

import pytest
from django.test import TestCase

from web.domains.importer.forms import (
    ImporterFilter,
    ImporterIndividualForm,
    ImporterOrganisationForm,
)
from web.models import Importer, User
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import UserFactory


class ImporterFilterTest(TestCase):
    def setUp(self):
        ImporterFactory(
            name="Archived Importer Organisation", type=Importer.ORGANISATION, is_active=False
        )
        ImporterFactory(
            name="Active Importer Organisation", type=Importer.ORGANISATION, is_active=True
        )
        ImporterFactory(
            name="Archived Individual Importer", type=Importer.INDIVIDUAL, is_active=False
        )
        ImporterFactory(name="Active Individual Importer", type=Importer.INDIVIDUAL, is_active=True)

    def run_filter(self, data=None):
        return ImporterFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({"name": "org"})
        self.assertEqual(results.count(), 2)

    def test_entity_type_filter(self):
        results = self.run_filter({"importer_entity_type": Importer.INDIVIDUAL})
        self.assertEqual(results.count(), 2 + 1)  # We have added one to use as a pytest fixture

    def test_filter_order(self):
        results = self.run_filter({"name": "import"})
        self.assertEqual(results.count(), 4 + 1)  # We have added one to use as a pytest fixture
        first = results.first()
        last = results.last()
        self.assertEqual(first.name, "Active Importer Organisation")
        self.assertEqual(last.name, "Archived Individual Importer")


def test_required_fields_importer_individual_form():
    """Assert fields required."""
    form = ImporterIndividualForm({})
    assert form.is_valid() is False
    assert "user" in form.errors
    assert "eori_number" in form.errors

    expected = "You must enter this item"
    assert expected in form.errors["user"]
    assert expected in form.errors["eori_number"]


def test_invalid_eori_number_importer_individual_form():
    """Assert eori number starts with prefix."""
    form = ImporterIndividualForm({"eori_number": "42"})

    assert form.is_valid() is False
    assert "eori_number" in form.errors
    error = "'42' doesn't start with GBPR"
    assert error in form.errors["eori_number"]


@pytest.mark.django_db()
def test_type_importer_individual_form():
    """Assert individual importer type is set on save."""
    user = UserFactory.create(account_status=User.ACTIVE, permission_codenames=["importer_access"])
    data = {"user": user.pk, "eori_number": "GBPR"}
    form = ImporterIndividualForm(data)

    assert form.is_valid(), form.errors
    form.save()

    importer = Importer.objects.last()
    assert importer.type == "INDIVIDUAL"


def test_required_fields_importer_organisation_form():
    """Assert fields required."""
    form = ImporterOrganisationForm({})
    assert form.is_valid() is False
    assert "name" in form.errors
    assert "eori_number" in form.errors

    expected = "You must enter this item"
    assert expected in form.errors["name"]
    assert expected in form.errors["eori_number"]


def test_invalid_eori_number_importer_organisation_form():
    """Assert eori number starts with prefix."""
    form = ImporterOrganisationForm({"eori_number": "42"})

    assert form.is_valid() is False
    assert "eori_number" in form.errors
    error = "'42' doesn't start with GB"
    assert error in form.errors["eori_number"]


@pytest.mark.django_db()
@patch("web.domains.importer.forms.api_get_company")
def test_type_importer_organisation_form(api_get_company):
    """Assert organisation importer type is set on save."""
    api_get_company.return_value = {
        "registered_office_address": {
            "address_line_1": "60 rue Wiertz",
            "postcode": "B-1047",
            "locality": "Bruxelles",
        }
    }

    data = {"name": "hello", "eori_number": "GB", "registered_number": "42"}
    form = ImporterOrganisationForm(data)

    assert form.is_valid(), form.errors
    form.save()

    importer = Importer.objects.last()
    assert importer.type == "INDIVIDUAL"
