from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case.models import CaseDocumentReference

from . import types


def fa_oil_serializer(
    application: OpenIndividualLicenceApplication, chief_id: str
) -> types.CreateLicenceData:
    """Return licence data to send to chief."""

    # TODO: ICMSLST-1657 - Work out correct importer
    importer = application.importer  # or application.agent

    # TODO: ICMSLST-1657 - Work out correct office
    office = application.importer_office  # or application.agent_office

    # TODO: ICMSLST-1658 Revisit this (see icms/web/utils/pdf/utils.py -> _get_importer_eori_numbers)
    eori_number = importer.eori_number or importer.eori_number_ni

    # TODO: ICMSLST-1659 We need a consistent way of saving address fields (this isn't accurate enough)
    address_lines = {
        f"line_{i}": line.strip("\r")
        for i, line in enumerate(office.address.split("\n")[:5], start=1)
    }

    organisation = types.OrganisationData(
        eori_number=eori_number,
        name=importer.name,
        address=types.AddressData(
            # max address lines is 5
            **address_lines,
            postcode=office.postcode,
        ),
        start_date=None,
        end_date=None,
    )

    licence = application.get_most_recent_licence()
    licence_ref: CaseDocumentReference = licence.document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )

    # fa-oil hard codes the value to any country so it is a group
    country_code = application.origin_country.hmrc_code
    endorsements = [e.content for e in application.endorsements.all()]

    licence_data = types.LicenceData(
        type="OIL",
        action="insert",
        id=chief_id,
        reference=licence_ref.reference,
        case_reference=application.reference,
        start_date=licence.licence_start_date,
        end_date=licence.licence_end_date,
        organisation=organisation,
        country_group=country_code,
        country_code="",
        restrictions="\n\n".join(endorsements),
        goods=[types.GoodsData(description=application.goods_description())],
    )

    return types.CreateLicenceData(licence=licence_data)
