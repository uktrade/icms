from typing import Any

from web.models import ImportApplication, OpenIndividualLicenceApplication

from .types import DocumentTypes


def get_fa_oil_licence_context(
    application: OpenIndividualLicenceApplication, doc_type: DocumentTypes
) -> dict[str, Any]:

    importer = application.importer
    office = application.importer_office

    return {
        "applicant_reference": application.applicant_reference,
        "importer_name": importer.display_name,
        "goods_description": application.goods_description(),
        "licence_start_date": _get_licence_start_date(application),
        "licence_end_date": _get_licence_end_date(application),
        "licence_number": _get_licence_number(application, doc_type),
        "eori_numbers": _get_importer_eori_numbers(application),
        "importer_address": office.address.split("\n"),
        "importer_postcode": office.postcode,
        # TODO: ICMSLST-1428 Revisit this - See nl2br
        "endorsements": [
            content.split("\r\n")
            for content in application.endorsements.all().values_list("content", flat=True)
        ],
    }


def _get_licence_start_date(application: ImportApplication):
    if application.licence_start_date:
        return application.licence_start_date.strftime("%d %B %Y")

    return "Licence Start Date not set"


def _get_licence_end_date(application: ImportApplication):
    if application.licence_end_date:
        return application.licence_end_date.strftime("%d %B %Y")

    return "Licence End Date not set"


def _get_licence_number(application: ImportApplication, doc_type: DocumentTypes) -> str:
    if doc_type == DocumentTypes.LICENCE_PRE_SIGN:
        return "ICMSLST-1224: Real Licence Number"

    return "[[Licence Number]]"


def _get_importer_eori_numbers(application) -> list[str]:
    # TODO: Check the Country of Consignment logic for other firearm licence types
    # TODO: If the applicant’s address has a BT (Belfast) post code AND the Country of Consignment is an EU country:

    importer = application.importer
    office = application.importer_office
    is_northern_ireland = office.postcode.upper().startswith("BT")

    # Use override if set
    main_eori_num = office.eori_number or importer.eori_number

    # EORI numbers to return
    eori_numbers = [main_eori_num]

    if is_northern_ireland:
        eori_numbers.append(f"XI{main_eori_num[2:]}")

    return eori_numbers
