from typing import TYPE_CHECKING

from web.domains.case._import.fa_dfl.models import DFLApplication
from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case.models import CaseDocumentReference

from . import types

if TYPE_CHECKING:
    from web.models import ImportApplication, Importer, Office


def fa_oil_serializer(
    application: OpenIndividualLicenceApplication, chief_id: str
) -> types.CreateLicenceData:
    """Return FA OIL licence data to send to chief."""

    organisation = _get_organisation(application)
    licence = application.get_most_recent_licence()
    licence_ref: CaseDocumentReference = licence.document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )

    # fa-oil hard codes the value to any country so it is a group
    country_code = application.origin_country.hmrc_code
    restrictions = _get_restrictions(application)

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
        restrictions=restrictions,
        goods=[types.GoodsData(description=application.goods_description())],
    )

    return types.CreateLicenceData(licence=licence_data)


def fa_dfl_serializer(application: DFLApplication, chief_id: str) -> types.CreateLicenceData:
    """Return FA DFL licence data to send to chief."""

    organisation = _get_organisation(application)
    licence = application.get_most_recent_licence()
    licence_ref: CaseDocumentReference = licence.document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )
    goods = [
        types.GoodsData(description=g.goods_description)
        for g in application.goods_certificates.all()
    ]

    licence_data = types.LicenceData(
        type="DFL",
        action="insert",
        id=chief_id,
        reference=licence_ref.reference,
        case_reference=application.reference,
        start_date=licence.licence_start_date,
        end_date=licence.licence_end_date,
        organisation=organisation,
        country_code=application.origin_country.hmrc_code,
        restrictions=_get_restrictions(application),
        goods=goods,
    )

    return types.CreateLicenceData(licence=licence_data)


def _get_organisation(application: "ImportApplication") -> types.OrganisationData:
    importer = _get_importer(application)
    office = _get_office(application)
    eori_number = _get_eori_number(importer)
    address_lines = _get_address_lines(office)

    return types.OrganisationData(
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


# TODO: ICMSLST-1657 - Work out correct importer
def _get_importer(application: "ImportApplication") -> "Importer":
    importer = application.importer  # or application.agent

    return importer


# TODO: ICMSLST-1657 - Work out correct office
def _get_office(application: "ImportApplication") -> "Office":
    office = application.importer_office  # or application.agent_office

    return office


# TODO: ICMSLST-1658 Revisit this (see icms/web/utils/pdf/utils.py -> _get_importer_eori_numbers)
def _get_eori_number(importer: "Importer") -> str:
    eori_number = importer.eori_number or importer.eori_number_ni

    return eori_number


# TODO: ICMSLST-1659 We need a consistent way of saving address fields (this isn't accurate enough)
def _get_address_lines(office: "Office") -> dict[str, str]:
    address_lines = {
        f"line_{i}": line.strip("\r")
        for i, line in enumerate(office.address.split("\n")[:5], start=1)
    }

    return address_lines


def _get_restrictions(application: "ImportApplication") -> str:
    endorsements = [e.content for e in application.endorsements.all()]

    return "\n\n".join(endorsements)
