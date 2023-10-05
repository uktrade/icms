import pytest
from django.utils import timezone

from web.models import (
    Country,
    DFLApplication,
    ExportApplicationCertificate,
    ImportApplicationLicence,
    Office,
    OpenIndividualLicenceApplication,
    SILApplication,
    Template,
)
from web.utils import day_ordinal_date


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
def certificate():
    return ExportApplicationCertificate()


@pytest.fixture()
def oil_expected_preview_context():
    """Returns the minimum expected context values - tests then override the different keys in the tests."""

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Test Importer 1",
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
        "eori_numbers": ["GB1111111111ABCDE"],
        "importer_address": ["22 Some Avenue", "Some Way", "Some Town"],
        "importer_postcode": "S93bl",  # /PS-IGNORE
        "endorsements": [],
        "issue_date": day_ordinal_date(timezone.now().date()),
        "page_title": "Licence Preview",
    }


@pytest.fixture()
def dfl_expected_preview_context():
    """Returns the minimum expected context values - tests then override the different keys in the tests."""

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Test Importer 1",
        "consignment_country": "Spain",
        "origin_country": "Italy",
        "goods": [],
        "licence_start_date": "Licence Start Date not set",
        "licence_end_date": "Licence End Date not set",
        "licence_number": "[[Licence Number]]",
        "eori_numbers": ["GB1111111111ABCDE"],
        "importer_address": ["22 Some Avenue", "Some Way", "Some Town"],
        "importer_postcode": "S93bl",  # /PS-IGNORE
        "endorsements": [],
        "issue_date": day_ordinal_date(timezone.now().date()),
        "page_title": "Licence Preview",
    }


@pytest.fixture()
def sil_expected_preview_context():
    """Returns the minimum expected context values - tests then override the different keys in the tests."""
    template = Template.objects.get(template_code="FIREARMS_MARKINGS_STANDARD")

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Test Importer 1",
        "consignment_country": "Poland",
        "origin_country": "Ireland",
        "goods": [],
        "licence_start_date": "Licence Start Date not set",
        "licence_end_date": "Licence End Date not set",
        "licence_number": "[[Licence Number]]",
        "eori_numbers": ["GB1111111111ABCDE"],
        "importer_address": ["22 Some Avenue", "Some Way", "Some Town"],
        "importer_postcode": "S93bl",  # /PS-IGNORE
        "endorsements": [],
        "markings_text": template.template_content,
        "issue_date": day_ordinal_date(timezone.now().date()),
        "page_title": "Licence Preview",
    }


@pytest.fixture()
def sanctions_expected_preview_context():
    """Returns the minimum expected context values - tests then override the different keys in the tests."""
    return {
        "page_title": "Licence Preview",
        "preview_licence": True,
        "importer_name": "Test Importer 1",
        "eori_numbers": ["GB0123456789ABCDE", "XI0123456789ABCDE"],
        "importer_address": ["I1 address line 1", "I1 address line 2"],
        "importer_postcode": "BT180LZ",  # /PS-IGNORE
        "endorsements": [],
        "licence_number": "[[Licence Number]]",
        "licence_start_date": "Licence Start Date not set",
        "licence_end_date": "Licence End Date not set",
        "country_of_manufacture": "Iran IR 616",
        "country_of_shipment": "Afghanistan AF 660",
        "ref": "applicant_reference value",
        "goods_list": [
            ["Test Goods, 2707100010, 1000 kilos, 10500"],
            ["More Commoditites, 7112990090, 56.78 kilos, 789"],
        ],
    }
