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
    assert results.count() == 2


@pytest.mark.django_db()
def test_filter_order():
    results = ImporterFilter(data={"name": "import"}).qs
    assert results.count() == 4
    assert results.first().user.username == "individual_importer_user"
    assert results.last().name == "Test Importer 3 Inactive"


def test_required_fields_importer_individual_form():
    """Assert fields required."""
    form = ImporterIndividualForm({})
    assert form.is_valid() is False
    assert "user" in form.errors

    expected = "You must enter this item"
    assert expected in form.errors["user"]


@pytest.mark.django_db()
def test_type_importer_individual_form(importer_one_contact):
    """Assert individual importer type is set on save."""

    data = {"user": importer_one_contact.pk, "eori_number": "GB123456789012"}
    form = ImporterIndividualForm(data)

    assert form.is_valid(), form.errors
    importer = form.save()

    assert importer.type == "INDIVIDUAL"
    assert importer.eori_number == "GB123456789012"


@pytest.mark.parametrize(
    "eori,err",
    [
        ("", "You must enter this item"),
        ("GBPR", "Must start with 'GB' followed by 12 or 15 numbers"),
        ("GB12345678901", "Must start with 'GB' followed by 12 or 15 numbers"),
        ("GB1234567890123", "Must start with 'GB' followed by 12 or 15 numbers"),
        ("AB1234567890123", "'AB1234567890123' doesn't start with GB"),
    ],
)
def test_individual_importer_eori_validation(importer_one_contact, eori, err):
    data = {"user": importer_one_contact.pk, "eori_number": eori}
    form = ImporterIndividualForm(data)
    assert form.is_valid() is False
    assert form.errors["eori_number"] == [err]


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


def test_invalid_eori_number_length_importer_organisation_form():
    """Assert eori number starts with prefix."""
    form = ImporterOrganisationForm({"eori_number": "GB12345"})

    assert form.is_valid() is False
    assert "eori_number" in form.errors
    error = "Must start with 'GB' followed by 12 or 15 numbers"
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

    data = {"name": "hello", "eori_number": "GB123456789012345", "registered_number": "42"}
    form = ImporterOrganisationForm(data)

    assert form.is_valid(), form.errors
    importer = form.save()

    assert importer.type == "ORGANISATION"


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

    data = {"name": "hello", "eori_number": "GB123456789012345", "registered_number": "42"}
    form = ImporterOrganisationForm(data)

    assert form.is_valid()
    assert form.company == api_get_company.return_value
