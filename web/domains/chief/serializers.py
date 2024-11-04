from typing import TYPE_CHECKING, Any, Literal, Protocol

from web.domains.case.services import document_pack
from web.flow.models import ProcessTypes
from web.forms.utils import clean_postcode
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

    CHIEF_APPLICATIONS = (
        SILApplication
        | DFLApplication
        | OpenIndividualLicenceApplication
        | SanctionsAndAdhocApplication
    )

CHIEF_ACTION = Literal["insert", "replace", "cancel"]
CHIEF_TYPES = Literal["OIL", "DFL", "SIL", "SAN"]


class ChiefSerializer(Protocol):
    """The protocol documenting all chief serializers"""

    def __call__(
        self,
        application: "CHIEF_APPLICATIONS",
        action: CHIEF_ACTION,
        chief_id: str,
    ) -> types.LicenceDataPayload: ...


def fix_licence_reference(process_type: str, licence_reference: str) -> str:
    """Fix the licence reference sent to CHIEF.

    For paper licences the prefix isn't stored, however CHIEF requires it in the payload.
    """

    if licence_reference.casefold().startswith("gb"):
        return licence_reference

    prefix = {
        ProcessTypes.FA_DFL: "SIL",
        ProcessTypes.FA_OIL: "OIL",
        ProcessTypes.FA_SIL: "SIL",
        ProcessTypes.SANCTIONS: "SAN",
        # Inactive application types
        ProcessTypes.SPS: "AOG",
        ProcessTypes.TEXTILES: "TEX",
    }
    xxx = prefix[process_type]  # type: ignore[index]

    return f"GB{xxx}{licence_reference}"


def cancel_licence_serializer(
    application: "CHIEF_APPLICATIONS", action: CHIEF_ACTION, chief_id: str
) -> types.LicenceDataPayload:
    doc_pack = document_pack.pack_revoked_get(application)
    licence_reference = fix_licence_reference(
        application.process_type, document_pack.doc_ref_licence_get(doc_pack).reference
    )

    licence_data = types.CancelLicencePayload(
        type=_get_type(application),
        action=action,  # type:ignore[arg-type]
        id=chief_id,
        reference=application.reference,
        licence_reference=licence_reference,
        start_date=doc_pack.licence_start_date,
        end_date=doc_pack.licence_end_date,
    )

    return types.LicenceDataPayload(licence=licence_data)


def sanction_serializer(
    application: "SanctionsAndAdhocApplication", action: CHIEF_ACTION, chief_id: str
) -> types.LicenceDataPayload:
    organisation = get_organisation(application)
    doc_pack = document_pack.pack_draft_get(application)
    licence_reference = fix_licence_reference(
        application.process_type, document_pack.doc_ref_licence_get(doc_pack).reference
    )

    sanction_goods: "QuerySet[SanctionsAndAdhocApplicationGoods]" = (
        application.sanctions_goods.all().select_related("commodity")
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
        type=_get_type(application),  # type:ignore[arg-type]
        action=action,  # type:ignore[arg-type]
        id=chief_id,
        reference=application.reference,
        licence_reference=licence_reference,
        start_date=doc_pack.licence_start_date,
        end_date=doc_pack.licence_end_date,
        organisation=organisation,
        restrictions=get_restrictions(application),
        goods=goods,
        **country_kwargs,
    )

    return types.LicenceDataPayload(licence=licence_data)


def fa_dfl_serializer(
    application: "DFLApplication", action: CHIEF_ACTION, chief_id: str
) -> types.LicenceDataPayload:
    """Return FA DFL licence data to send to chief."""

    organisation = get_organisation(application)
    doc_pack = document_pack.pack_draft_get(application)
    licence_reference = fix_licence_reference(
        application.process_type, document_pack.doc_ref_licence_get(doc_pack).reference
    )

    goods = [
        types.FirearmGoodsData(description=g.goods_description)
        for g in application.goods_certificates.filter(is_active=True)
    ]

    country_kwargs = _get_country_kwargs(application.origin_country.hmrc_code)

    licence_data = types.FirearmLicenceData(
        type=_get_type(application),  # type:ignore[arg-type]
        action=action,  # type:ignore[arg-type]
        id=chief_id,
        reference=application.reference,
        licence_reference=licence_reference,
        start_date=doc_pack.licence_start_date,
        end_date=doc_pack.licence_end_date,
        organisation=organisation,
        restrictions=get_restrictions(application),
        goods=goods,
        **country_kwargs,
    )

    return types.LicenceDataPayload(licence=licence_data)


def fa_oil_serializer(
    application: "OpenIndividualLicenceApplication", action: CHIEF_ACTION, chief_id: str
) -> types.LicenceDataPayload:
    """Return FA OIL licence data to send to chief."""

    organisation = get_organisation(application)
    doc_pack = document_pack.pack_draft_get(application)
    licence_reference = fix_licence_reference(
        application.process_type, document_pack.doc_ref_licence_get(doc_pack).reference
    )

    # fa-oil hard codes the value to any country therefore it is a group
    country_group_code = application.origin_country.hmrc_code
    restrictions = get_restrictions(application)

    licence_data = types.FirearmLicenceData(
        type=_get_type(application),  # type:ignore[arg-type]
        action=action,  # type:ignore[arg-type]
        id=chief_id,
        reference=application.reference,
        licence_reference=licence_reference,
        start_date=doc_pack.licence_start_date,
        end_date=doc_pack.licence_end_date,
        organisation=organisation,
        country_group=country_group_code,
        restrictions=restrictions,
        goods=[types.FirearmGoodsData(description=application.goods_description())],
    )

    return types.LicenceDataPayload(licence=licence_data)


def fa_sil_serializer(
    application: "SILApplication", action: CHIEF_ACTION, chief_id: str
) -> types.LicenceDataPayload:
    organisation = get_organisation(application)
    doc_pack = document_pack.pack_draft_get(application)
    licence_reference = fix_licence_reference(
        application.process_type, document_pack.doc_ref_licence_get(doc_pack).reference
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
            _get_section_58_other_goods(application.goods_section582_others.filter(is_active=True))
        )

    country_kwargs = _get_country_kwargs(application.origin_country.hmrc_code)

    licence_data = types.FirearmLicenceData(
        type=_get_type(application),  # type:ignore[arg-type]
        action=action,  # type:ignore[arg-type]
        id=chief_id,
        reference=application.reference,
        licence_reference=licence_reference,
        start_date=doc_pack.licence_start_date,
        end_date=doc_pack.licence_end_date,
        organisation=organisation,
        restrictions=get_restrictions(application),
        goods=goods,
        **country_kwargs,
    )

    return types.LicenceDataPayload(licence=licence_data)


def _get_section_goods(goods_qs, section):
    return [
        types.FirearmGoodsData(
            description=f"{g.description} to which {section} of the Firearms Act 1968, as amended, applies.",
            quantity=g.quantity,
            controlled_by=(
                types.ControlledByEnum.OPEN
                if g.unlimited_quantity
                else types.ControlledByEnum.QUANTITY
            ),
            unit=types.QuantityCodeEnum.NUMBER,
        )
        for g in goods_qs
    ]


def _get_section_5_goods(goods_qs: "QuerySet[SILGoodsSection5]") -> list[types.FirearmGoodsData]:
    goods = []

    for g in goods_qs:
        section = f"Section {g.section_5_clause.clause}"
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


def _get_section_58_obsolete_goods(
    goods_qs: "QuerySet[SILGoodsSection582Obsolete]",  # /PS-IGNORE
) -> list[types.FirearmGoodsData]:
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


def _get_section_58_other_goods(goods_qs):
    return [
        types.FirearmGoodsData(
            description=f"{g.description} to which Section 58(2) of the Firearms Act 1968, as amended, applies.",
            quantity=g.quantity,
            controlled_by=types.ControlledByEnum.QUANTITY,
            unit=types.QuantityCodeEnum.NUMBER,
        )
        for g in goods_qs
    ]


def _get_type(application: "CHIEF_APPLICATIONS") -> CHIEF_TYPES:
    match application.process_type:
        case ProcessTypes.FA_OIL:
            return "OIL"
        case ProcessTypes.FA_DFL:
            return "DFL"
        case ProcessTypes.FA_SIL:
            return "SIL"
        case ProcessTypes.SANCTIONS:
            return "SAN"
        case _:
            raise ValueError(f"Unknown process type: {application.process_type}")


def get_organisation(application: "ImportApplication") -> types.OrganisationData:
    importer = _get_importer(application)
    office = _get_office(application)
    eori_number = _get_eori_number(importer, office)
    address_lines = _get_address_lines(office)

    if not importer.is_organisation():
        name = importer.user.full_name
    else:
        name = importer.name

    return types.OrganisationData(
        eori_number=eori_number,
        name=name,
        address=types.AddressData(
            # max address lines is 5
            **address_lines,
            postcode=clean_postcode(office.postcode),
        ),
        start_date=None,
        end_date=None,
    )


def _get_importer(application: "ImportApplication") -> "Importer":
    """ICMS V1 always sends the main importer details to CHIEF (Even if an agent is also chosen)"""

    importer = application.importer

    return importer


def _get_office(application: "ImportApplication") -> "Office":
    """ICMS V1 always sends the main importer office details to CHIEF (Even if an agent is also chosen)"""

    office = application.importer_office

    return office


def _get_eori_number(importer: "Importer", office: "Office") -> str:
    # Use office override if set
    main_eori_number = office.eori_number or importer.eori_number

    return main_eori_number


def _get_address_lines(office: "Office") -> dict[str, str]:
    return {
        "line_1": _get_address_line(office.address_1),
        "line_2": _get_address_line(office.address_2),
        "line_3": _get_address_line(office.address_3),
        "line_4": _get_address_line(office.address_4),
        "line_5": _get_address_line(office.address_5),
    }


def _get_address_line(line: str | None) -> str:
    """Return a chief formatted address line.

    The CHIEF API limits each line to 35 characters.
    For legacy data migration reasons we may be storing more than 35 characters in each
    address line.
    """

    if not line:
        return ""

    return line[:35]


def get_restrictions(application: "ImportApplication", *, limit: int = 2000) -> str:
    """Return application restrictions.

    :param application: Application being sent to CHIEF
    :param limit: The max number of characters we can send to CHIEF, it can never be more than 2000.
    """

    endorsements = application.endorsements.values_list("content", flat=True).order_by(
        "created_datetime"
    )
    text = "\n".join(endorsements)

    # "<trc>" matches what ICMS V1 does when sending endorsements to CHIEF.
    return text if len(text) <= limit else text[: limit - 5] + "<trc>"


def _get_country_kwargs(code: str) -> dict[str, str]:
    if len(code) == 2:
        return {"country_code": code}
    else:
        return {"country_group": code}
