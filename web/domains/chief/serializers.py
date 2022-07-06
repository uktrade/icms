from typing import TYPE_CHECKING, Any

from web.domains.case.models import CaseDocumentReference
from web.utils.commodity import annotate_commodity_unit

from . import types

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.models import SILGoodsSection582Obsolete  # /PS-IGNORE
    from web.models import (
        DFLApplication,
        ImportApplication,
        Importer,
        Office,
        OpenIndividualLicenceApplication,
        SanctionsAndAdhocApplication,
        SanctionsAndAdhocApplicationGoods,
        SILApplication,
        SILGoodsSection5,
    )


def sanction_serializer(
    application: "SanctionsAndAdhocApplication", chief_id: str
) -> types.CreateLicenceData:
    organisation = _get_organisation(application)
    licence = application.get_most_recent_licence()
    licence_ref: CaseDocumentReference = licence.document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )

    sanction_goods: "QuerySet[SanctionsAndAdhocApplicationGoods]" = (
        application.sanctionsandadhocapplicationgoods_set.all().select_related("commodity")
    )
    goods_qs = annotate_commodity_unit(sanction_goods, "commodity__").distinct()

    goods = [
        types.SanctionGoodsData(
            commodity=g.commodity.commodity_code,
            quantity=g.quantity_amount,
            unit=g.hmrc_code,  # This is an annotation
        )
        for g in goods_qs
    ]

    country_kwargs = _get_country_kwargs(application.origin_country.hmrc_code)
    licence_data = types.SanctionsLicenceData(
        type="SAN",
        action="insert",
        id=chief_id,
        reference=licence_ref.reference,
        case_reference=application.reference,
        start_date=licence.licence_start_date,
        end_date=licence.licence_end_date,
        organisation=organisation,
        restrictions=_get_restrictions(application),
        goods=goods,
        **country_kwargs,
    )

    return types.CreateLicenceData(licence=licence_data)


def fa_dfl_serializer(application: "DFLApplication", chief_id: str) -> types.CreateLicenceData:
    """Return FA DFL licence data to send to chief."""

    organisation = _get_organisation(application)
    licence = application.get_most_recent_licence()
    licence_ref: CaseDocumentReference = licence.document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )
    goods = [
        types.FirearmGoodsData(description=g.goods_description)
        for g in application.goods_certificates.all()
    ]

    country_kwargs = _get_country_kwargs(application.origin_country.hmrc_code)
    licence_data = types.FirearmLicenceData(
        type="DFL",
        action="insert",
        id=chief_id,
        reference=licence_ref.reference,
        case_reference=application.reference,
        start_date=licence.licence_start_date,
        end_date=licence.licence_end_date,
        organisation=organisation,
        restrictions=_get_restrictions(application),
        goods=goods,
        **country_kwargs,
    )

    return types.CreateLicenceData(licence=licence_data)


def fa_oil_serializer(
    application: "OpenIndividualLicenceApplication", chief_id: str
) -> types.CreateLicenceData:
    """Return FA OIL licence data to send to chief."""

    organisation = _get_organisation(application)
    licence = application.get_most_recent_licence()
    licence_ref: CaseDocumentReference = licence.document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )

    # fa-oil hard codes the value to any country therefore it is a group
    country_group_code = application.origin_country.hmrc_code
    restrictions = _get_restrictions(application)

    licence_data = types.FirearmLicenceData(
        type="OIL",
        action="insert",
        id=chief_id,
        reference=licence_ref.reference,
        case_reference=application.reference,
        start_date=licence.licence_start_date,
        end_date=licence.licence_end_date,
        organisation=organisation,
        country_group=country_group_code,
        restrictions=restrictions,
        goods=[types.FirearmGoodsData(description=application.goods_description())],
    )

    return types.CreateLicenceData(licence=licence_data)


def fa_sil_serializer(application: "SILApplication", chief_id: str) -> types.CreateLicenceData:
    organisation = _get_organisation(application)
    licence = application.get_most_recent_licence()
    licence_ref: CaseDocumentReference = licence.document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )

    goods = []

    if application.section1:
        goods.extend(
            _get_section_goods(application.goods_section1.filter(is_active=True), "Section 1")
        )

    if application.section2:
        goods.extend(
            _get_section_goods(application.goods_section2.filter(is_active=True), "Section 2")
        )

    if application.section5:
        goods.extend(_get_section_5_goods(application.goods_section5.filter(is_active=True)))

    if application.section58_obsolete:
        goods.extend(
            _get_section_58_obsolete_goods(
                application.goods_section582_obsoletes.filter(is_active=True)
            )
        )

    if application.section58_other:
        goods.extend(
            _get_section_goods(
                application.goods_section582_others.filter(is_active=True), "Section 58(2)"
            )
        )

    country_kwargs = _get_country_kwargs(application.origin_country.hmrc_code)
    licence_data = types.FirearmLicenceData(
        type="SIL",
        action="insert",
        id=chief_id,
        reference=licence_ref.reference,
        case_reference=application.reference,
        start_date=licence.licence_start_date,
        end_date=licence.licence_end_date,
        organisation=organisation,
        restrictions=_get_restrictions(application),
        goods=goods,
        **country_kwargs,
    )

    return types.CreateLicenceData(licence=licence_data)


def _get_section_goods(goods_qs, section):
    return [
        types.FirearmGoodsData(
            description=f"{g.description} to which {section} of the Firearms Act 1968, as amended, applies.",
            quantity=g.quantity,
            controlled_by=types.ControlledByEnum.QUANTITY,
            unit=types.QuantityCodeEnum.NUMBER,
        )
        for g in goods_qs
    ]


def _get_section_5_goods(goods_qs: "QuerySet[SILGoodsSection5]"):
    goods = []

    for g in goods_qs:
        # TODO: Revisit when implementing ICMSLT-1686
        # This shouldn't use the full subsection but they are currently hardcoded.
        # The hardcoded list needs resolving before we can fix this.
        section = f"Section 5({g.subsection})"
        description = (
            f"{g.description} to which {section} of the Firearms Act 1968, as amended, applies."
        )

        if g.unlimited_quantity:
            kwargs: dict[str, Any] = {"controlled_by": types.ControlledByEnum.OPEN}
        else:
            kwargs = {
                "quantity": g.quantity,
                "controlled_by": types.ControlledByEnum.QUANTITY,
                "unit": types.QuantityCodeEnum.NUMBER,
            }

        goods.append(types.FirearmGoodsData(description=description, **kwargs))

    return goods


def _get_section_58_obsolete_goods(goods_qs: "QuerySet[SILGoodsSection582Obsolete]"):  # /PS-IGNORE
    goods = []

    for g in goods_qs:
        gd = g.description
        oc = g.obsolete_calibre
        description = (
            f"{gd} chambered in the obsolete calibre {oc} to which Section 58(2)"
            f" of the Firearms Act 1968, as amended, applies."
        )

        goods.append(
            types.FirearmGoodsData(
                description=description,
                quantity=g.quantity,
                controlled_by=types.ControlledByEnum.QUANTITY,
                unit=types.QuantityCodeEnum.NUMBER,
            )
        )

    return goods


def _get_fa_sil_description(goods_description: str, section: str) -> str:
    return f"{goods_description} to which {section} of the Firearms Act 1968, as amended, applies."


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


def _get_country_kwargs(code) -> dict[str, str]:
    if len(code) == 2:
        return {"country_code": code}
    else:
        return {"country_group": code}
