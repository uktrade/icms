import pytest
from django.utils import timezone

from web.models import (
    Country,
    DFLApplication,
    ImportApplicationLicence,
    Importer,
    Office,
    OpenIndividualLicenceApplication,
    SILApplication,
    Template,
)


@pytest.fixture()
def importer():
    return Importer(eori_number="GB123456789", type=Importer.ORGANISATION, name="Importer Name")


@pytest.fixture()
def importer_office():
    return Office(
        address_1="22 Some Avenue",
        address_2="Some Way",
        address_3="Some Town",
        postcode="S93bl",  # /PS-IGNORE
    )


@pytest.fixture()
def oil_app(importer, importer_office):
    oil_app = OpenIndividualLicenceApplication(
        applicant_reference="Applicant Reference",
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        importer=importer,
        importer_office=importer_office,
    )

    return oil_app


@pytest.fixture()
def dfl_app(importer, importer_office):
    dfl_app = DFLApplication(
        applicant_reference="Applicant Reference",
        process_type=DFLApplication.PROCESS_TYPE,
        importer=importer,
        importer_office=importer_office,
        consignment_country=Country(name="Spain"),
        origin_country=Country(name="Italy"),
    )

    return dfl_app


@pytest.fixture()
def sil_app(importer, importer_office):
    sil_app = SILApplication(
        applicant_reference="Applicant Reference",
        process_type=SILApplication.PROCESS_TYPE,
        importer=importer,
        importer_office=importer_office,
        consignment_country=Country(name="Poland"),
        origin_country=Country(name="Ireland"),
        military_police=False,
        eu_single_market=False,
        manufactured=False,
    )

    return sil_app


@pytest.fixture()
def licence():
    return ImportApplicationLicence()


@pytest.fixture()
def oil_expected_preview_context():
    """Returns the minimum expected context values - tests then override the different keys in the tests."""

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Importer Name",
        "consignment_country": "Any Country",
        "origin_country": "Any Country",
        "goods_description": (
            "Firearms, component parts thereof, or ammunition of any applicable "
            "commodity code, other than those falling under Section 5 of the "
            "Firearms Act 1968 as amended."
        ),
        "licence_start_date": "Licence Start Date not set",
        "licence_end_date": "Licence End Date not set",
        "licence_number": "[[Licence Number]]",
        "eori_numbers": ["GB123456789"],
        "importer_address": ["22 Some Avenue", "Some Way", "Some Town"],
        "importer_postcode": "S93bl",  # /PS-IGNORE
        "endorsements": [],
        "issue_date": timezone.now().date().strftime("%d %B %Y"),
        "page_title": "Licence Preview",
    }


@pytest.fixture()
def dfl_expected_preview_context():
    """Returns the minimum expected context values - tests then override the different keys in the tests."""

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Importer Name",
        "consignment_country": "Spain",
        "origin_country": "Italy",
        "goods": [],
        "licence_start_date": "Licence Start Date not set",
        "licence_end_date": "Licence End Date not set",
        "licence_number": "[[Licence Number]]",
        "eori_numbers": ["GB123456789"],
        "importer_address": ["22 Some Avenue", "Some Way", "Some Town"],
        "importer_postcode": "S93bl",  # /PS-IGNORE
        "endorsements": [],
        "issue_date": timezone.now().date().strftime("%d %B %Y"),
        "page_title": "Licence Preview",
    }


@pytest.fixture()
def sil_expected_preview_context():
    """Returns the minimum expected context values - tests then override the different keys in the tests."""
    template = Template.objects.get(template_code="FIREARMS_MARKINGS_STANDARD")

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Importer Name",
        "consignment_country": "Poland",
        "origin_country": "Ireland",
        "goods": [],
        "licence_start_date": "Licence Start Date not set",
        "licence_end_date": "Licence End Date not set",
        "licence_number": "[[Licence Number]]",
        "eori_numbers": ["GB123456789"],
        "importer_address": ["22 Some Avenue", "Some Way", "Some Town"],
        "importer_postcode": "S93bl",  # /PS-IGNORE
        "endorsements": [],
        "markings_text": template.template_content,
        "issue_date": timezone.now().date().strftime("%d %B %Y"),
        "page_title": "Licence Preview",
    }
