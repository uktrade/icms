from unittest.mock import patch

import pytest

from web.domains.importer.forms import (
    ImporterFilter,
    ImporterIndividualForm,
    ImporterOrganisationForm,
)
from web.errors import CompanyNotFound
from web.models import Importer


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

    expected = "You must enter this item"
    assert expected in form.errors["user"]


def test_invalid_eori_number_importer_individual_form():
    """Assert eori number starts with prefix."""
    form = ImporterIndividualForm({"eori_number": "42"})

    assert form.is_valid() is False
    assert "eori_number" in form.errors
    error = "'42' doesn't start with GBPR"
    assert error in form.errors["eori_number"]


@pytest.mark.django_db()
def test_type_importer_individual_form(importer_one_contact):
    """Assert individual importer type is set on save."""

    data = {"user": importer_one_contact.pk, "eori_number": "GBPR"}
    form = ImporterIndividualForm(data)

    assert form.is_valid(), form.errors
    importer = form.save()

    assert importer.type == "INDIVIDUAL"


def test_required_fields_importer_organisation_form():
    """Assert fields required."""
    form = ImporterOrganisationForm({})
    assert form.is_valid() is False
    assert "name" in form.errors

    expected = "You must enter this item"
    assert expected in form.errors["name"]


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


@pytest.mark.django_db()
def test_eori_number_required_importer_individual_form(importer):
    """Assert the EORI number field is required when they already have one."""
    importer.eori_number = "GBPR234234"
    importer.save()
    form = ImporterIndividualForm(instance=importer, data={"eori_number": ""})

    assert not form.is_valid()
    assert "eori_number" in form.errors
    error = "You must enter this item"
    assert error in form.errors["eori_number"]


@pytest.mark.django_db()
def test_eori_number_not_required_importer_individual_form(importer, importer_one_contact):
    """Assert the EORI number field is not required when they don't already have one."""
    importer.eori_number = None
    importer.save()
    form = ImporterIndividualForm(
        instance=importer, data={"eori_number": "", "user": importer_one_contact.pk}
    )

    assert form.is_valid()


@pytest.mark.django_db()
@patch("web.domains.importer.forms.api_get_company")
def test_eori_number_required_importer_organisation_form(api_get_company, importer):
    """Assert the EORI number field is required when they already have one."""
    api_get_company.return_value = None
    data = {"name": "hello", "eori_number": "", "registered_number": "42"}
    form = ImporterOrganisationForm(instance=importer, data=data)

    assert not form.is_valid()
    assert "eori_number" in form.errors
    error = "You must enter this item"
    assert error in form.errors["eori_number"]


@pytest.mark.django_db()
@patch("web.domains.importer.forms.api_get_company")
def test_eori_number_not_required_importer_organisation_form(api_get_company, importer):
    """Assert the EORI number field is not required when they don't already have one."""
    api_get_company.return_value = {
        "registered_office_address": {
            "address_line_1": "60 rue Wiertz",
            "postcode": "B-1047",
            "locality": "Bruxelles",
        }
    }

    importer.eori_number = None
    importer.save()
    data = {"name": "hello", "eori_number": "", "registered_number": "42"}
    form = ImporterOrganisationForm(instance=importer, data=data)

    assert form.is_valid()


@pytest.mark.django_db()
@patch("web.domains.importer.forms.api_get_company")
def test_eori_number_required_new_importer_organisation_form(api_get_company):
    """Assert the EORI number field required when it's a newly created Importer."""
    api_get_company.return_value = None
    data = {"name": "hello", "eori_number": "", "registered_number": "42"}
    form = ImporterOrganisationForm(data=data)

    assert not form.is_valid()
    assert "eori_number" in form.errors
    error = "You must enter this item"
    assert error in form.errors["eori_number"]


@pytest.mark.django_db()
def test_eori_number_required_new_importer_individual_form(importer_one_contact):
    """Assert the EORI number field required when it's a newly created Importer."""
    data = {"user": importer_one_contact.pk, "eori_number": ""}
    form = ImporterIndividualForm(data)

    assert not form.is_valid()
    assert "eori_number" in form.errors
    error = "You must enter this item"
    assert error in form.errors["eori_number"]


@pytest.mark.django_db()
@patch("web.domains.importer.forms.api_get_company")
def test_invalid_company_number_okay(api_get_company, importer):
    """Assert that an invalid company number can be saved."""
    api_get_company.side_effect = CompanyNotFound()

    data = {"name": importer.name, "eori_number": importer.eori_number, "registered_number": "42"}
    form = ImporterOrganisationForm(instance=importer, data=data)
    assert form.is_valid()
    assert not form.company


@pytest.mark.django_db()
@patch("web.domains.importer.forms.api_get_company")
def test_valid_company_number_okay(api_get_company):
    """Assert that if the company number is perceived to be valid, the dict is assigned to form.company."""
    api_get_company.return_value = {
        "registered_office_address": {
            "address_line_1": "60 rue Wiertz",
            "postcode": "B-1047",
            "locality": "Bruxelles",
        }
    }

    data = {"name": "hello", "eori_number": "GB", "registered_number": "42"}
    form = ImporterOrganisationForm(data)

    assert form.is_valid()
    assert form.company == api_get_company.return_value
