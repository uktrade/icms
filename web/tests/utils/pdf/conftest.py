import pytest
from django.conf import settings
from django.utils import timezone

from web.models import (
    Commodity,
    Country,
    DFLApplication,
    ExportApplicationCertificate,
    ImportApplicationLicence,
    Office,
    OpenIndividualLicenceApplication,
    SanctionsAndAdhocApplicationGoods,
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
def sanctions_app(sanctions_app_submitted):
    commodity = Commodity.objects.get(commodity_code="2715000000")
    SanctionsAndAdhocApplicationGoods.objects.create(
        import_application_id=sanctions_app_submitted.pk,
        commodity=commodity,
        goods_description="Light Goods",
        quantity_amount=1.000,
        value=100.00,
        goods_description_original="Light Goods",
        quantity_amount_original=1.000,
        value_original=100.00,
    )
    commodity = Commodity.objects.get(commodity_code="2710199990")
    SanctionsAndAdhocApplicationGoods.objects.create(
        import_application_id=sanctions_app_submitted.pk,
        commodity=commodity,
        goods_description="Heavy Goods",
        quantity_amount=10000.000,
        value=9876.00,
        goods_description_original="Heavy Goods",
        quantity_amount_original=10000.000,
        value_original=9876.00,
    )
    return sanctions_app_submitted


@pytest.fixture()
def licence():
    return ImportApplicationLicence()


@pytest.fixture()
def certificate():
    return ExportApplicationCertificate()


@pytest.fixture()
def oil_expected_preview_context(active_signature):
    """Returns the minimum expected context values - tests then override the different keys in the tests."""

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Test Importer 1",
        "commodity_code": "ex Chapter 93",
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
        "signature": active_signature,
        "signature_file": "",
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    }


@pytest.fixture()
def dfl_expected_preview_context(active_signature):
    """Returns the minimum expected context values - tests then override the different keys in the tests."""

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Test Importer 1",
        "commodity_code": "ex Chapter 93",
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
        "signature": active_signature,
        "signature_file": "",
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    }


@pytest.fixture()
def sil_expected_preview_context(active_signature):
    """Returns the minimum expected context values - tests then override the different keys in the tests."""
    template = Template.objects.get(template_code=Template.Codes.FIREARMS_MARKINGS_STANDARD)

    return {
        "applicant_reference": "Applicant Reference",
        "importer_name": "Test Importer 1",
        "commodity_code": "ex Chapter 93",
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
        "signature": active_signature,
        "signature_file": "",
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    }


@pytest.fixture()
def sanctions_expected_preview_context(active_signature):
    """Returns the minimum expected context values - tests then override the different keys in the tests."""
    return {
        "preview_licence": True,
        "importer_name": "Test Importer 1",
        "eori_numbers": ["GB0123456789ABCDE"],
        "importer_address": ["I1 address line 1", "I1 address line 2"],
        "importer_postcode": "BT180LZ",  # /PS-IGNORE
        "endorsements": [],
        "licence_number": "[[Licence Number]]",
        "licence_start_date": "Licence Start Date not set",
        "licence_end_date": "Licence End Date not set",
        "country_of_manufacture": "Belarus BY 73",
        "country_of_shipment": "Afghanistan AF 660",
        "ref": "applicant_reference value",
        "goods_list": [
            ["Test Goods, 4202199090, 1000 pieces, 10500"],
            ["More Commoditites, 9013109000, 56.78 units, 789"],
            ["Light Goods, 2715000000, 1 Kilogramme, 100"],
            ["Heavy Goods, 2710199990, 10000 Kilogrammes, 9876"],
        ],
        "signature": active_signature,
        "signature_file": "",
    }


@pytest.fixture()
def wood_expected_preview_context(active_signature):
    """Returns the minimum expected context values - tests then override the different keys in the tests."""
    return {
        "preview_licence": True,
        "importer_name": "Test Importer 1",
        "eori_numbers": ["GB0123456789ABCDE"],
        "importer_address": ["I1 address line 1", "I1 address line 2"],
        "importer_postcode": "BT180LZ",  # /PS-IGNORE
        "endorsements": [],
        "licence_number": "[[Licence Number]]",
        "licence_start_date": "Licence Start Date not set",
        "licence_end_date": "Licence End Date not set",
        "ref": "Wood App Reference",
        "exporter_name": "Some Exporter",
        "exporter_address": ["Some Exporter Address"],
        "exporter_vat_number": "123456789",
        "quantity": "43",
        "goods": "Very Woody",
        "commodity_code": "4401310000",
        "signature": active_signature,
        "signature_file": "",
    }
