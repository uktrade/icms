from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group

from web.domains.importer.forms import (
    ImporterFilter,
    ImporterIndividualForm,
    ImporterOrganisationForm,
)
from web.models import Importer, User
from web.permissions import Perms
from web.tests.domains.user.factory import UserFactory


@pytest.mark.django_db()
def test_name_filter():
    results = ImporterFilter(data={"name": "importer 1"}).qs
    assert results.count() == 1


@pytest.mark.django_db()
def test_entity_type_filter():
    results = ImporterFilter(data={"importer_entity_type": Importer.INDIVIDUAL}).qs
    assert results.count() == 1


@pytest.mark.django_db()
def test_filter_order():
    results = ImporterFilter(data={"name": "import"}).qs
    assert results.count() == 3
    assert results.first().name == "Test Importer 1"
    assert results.last().name == "Test Importer 3 Inactive"


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
    user = UserFactory.create(account_status=User.ACTIVE)
    user.groups.add(Group.objects.get(name=Perms.obj.importer.get_group_name()))

    data = {"user": user.pk, "eori_number": "GBPR"}
    form = ImporterIndividualForm(data)

    assert form.is_valid(), form.errors
    importer = form.save()

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
    importer = form.save()

    assert importer.type == "ORGANISATION"
