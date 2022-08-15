from typing import TYPE_CHECKING, Any, Union

from web.domains.case.models import CaseDocumentReference

from .types import DocumentTypes

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.domains.case._import.fa_dfl.models import DFLApplication
    from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
    from web.domains.case._import.fa_sil import models as sil_models
    from web.domains.case._import.models import ImportApplicationLicence
    from web.models import ImportApplication

    SILGoods = Union[
        sil_models.SILGoodsSection1,
        sil_models.SILGoodsSection2,
        sil_models.SILGoodsSection5,
        sil_models.SILGoodsSection582Obsolete,  # /PS-IGNORE
        sil_models.SILGoodsSection582Other,  # /PS-IGNORE
    ]


def get_fa_oil_licence_context(
    application: "OpenIndividualLicenceApplication",
    licence: "ImportApplicationLicence",
    doc_type: DocumentTypes,
) -> dict[str, Any]:

    importer = application.importer
    office = application.importer_office

    return {
        "applicant_reference": application.applicant_reference,
        "importer_name": importer.display_name,
        "consignment_country": "Any Country",
        "origin_country": "Any Country",
        "goods_description": application.goods_description(),
        "licence_start_date": _get_licence_start_date(licence),
        "licence_end_date": _get_licence_end_date(licence),
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


def get_fa_dfl_licence_context(
    application: "DFLApplication", licence: "ImportApplicationLicence", doc_type: DocumentTypes
) -> dict[str, Any]:
    importer = application.importer
    office = application.importer_office

    return {
        "applicant_reference": application.applicant_reference,
        "importer_name": importer.display_name,
        "consignment_country": application.consignment_country.name,
        "origin_country": application.origin_country.name,
        "goods": _get_fa_dfl_goods(application),
        "licence_start_date": _get_licence_start_date(licence),
        "licence_end_date": _get_licence_end_date(licence),
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


def get_fa_sil_licence_context(
    application: "sil_models.SILApplication",
    licence: "ImportApplicationLicence",
    doc_type: DocumentTypes,
) -> dict[str, Any]:
    importer = application.importer
    office = application.importer_office

    return {
        "applicant_reference": application.applicant_reference,
        "importer_name": importer.display_name,
        "consignment_country": application.consignment_country.name,
        "origin_country": application.origin_country.name,
        "goods": _get_fa_sil_goods(application),
        "licence_start_date": _get_licence_start_date(licence),
        "licence_end_date": _get_licence_end_date(licence),
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


def _get_fa_dfl_goods(application: "DFLApplication") -> list[str]:
    return [
        g.goods_description
        for g in application.goods_certificates.all().order_by("created_datetime")
    ]


def _get_fa_sil_goods(application: "sil_models.SILApplication") -> list[tuple[str, int]]:
    """Return all related goods."""

    section_label_pairs = (
        ("goods_section1", "to which Section 1 of the Firearms Act 1968, as amended, applies."),
        ("goods_section2", "to which Section 2 of the Firearms Act 1968, as amended, applies."),
        (
            "goods_section5",
            "to which Section 5(1)(ac) of the Firearms Act 1968, as amended, applies.",
        ),
        (
            "goods_section582_others",
            "to which Section 58(2) of the Firearms Act 1968, as amended, applies.",
        ),
        (
            "goods_section582_obsoletes",
            "to which Section 58(2) of the Firearms Act 1968, as amended, applies.",
        ),
    )

    fa_sil_goods = []

    for goods_section, label_suffix in section_label_pairs:
        related_manager = getattr(application, goods_section)
        active_goods = related_manager.filter(is_active=True)
        fa_sil_goods.extend(get_fa_sil_goods_item(goods_section, active_goods, label_suffix))

    return fa_sil_goods


def get_fa_sil_goods_item(
    goods_section: str, active_goods: "QuerySet[SILGoods]", label_suffix: str
) -> list[tuple[str, int]]:
    if goods_section in ["goods_section1", "goods_section2", "goods_section582_others"]:
        return [(f"{g.description} {label_suffix}", g.quantity) for g in active_goods]

    elif goods_section == "goods_section5":
        goods = []

        for g in active_goods:
            quantity = "Unlimited" if g.unlimited_quantity else g.quantity
            goods.append((f"{g.description} {label_suffix}", quantity))

        return goods

    elif goods_section == "goods_section582_obsoletes":
        return [
            (
                f"{g.description} chambered in the obsolete calibre {g.obsolete_calibre} {label_suffix}",
                g.quantity,
            )
            for g in active_goods
        ]

    return []


def _get_licence_start_date(licence: "ImportApplicationLicence"):
    if licence.licence_start_date:
        return licence.licence_start_date.strftime("%d %B %Y")

    return "Licence Start Date not set"


def _get_licence_end_date(licence: "ImportApplicationLicence"):
    if licence.licence_end_date:
        return licence.licence_end_date.strftime("%d %B %Y")

    return "Licence End Date not set"


def _get_licence_number(application: "ImportApplication", doc_type: DocumentTypes) -> str:
    # TODO: ICMSLST-697 Revisit when signing the document (it may need its own context / template)
    if doc_type in (DocumentTypes.LICENCE_PRE_SIGN, DocumentTypes.LICENCE_SIGNED):
        licence = application.get_most_recent_licence()
        licence_doc = licence.document_references.get(
            document_type=CaseDocumentReference.Type.LICENCE
        )

        return licence_doc.reference

    return "[[Licence Number]]"


def _get_importer_eori_numbers(application) -> list[str]:
    # TODO: Check the Country of Consignment logic for other firearm licence types
    # TODO: If the applicant’s address has a BT (Belfast) post code AND the Country of Consignment is an EU country:

    importer = application.importer
    office = application.importer_office
    postcode = office.postcode
    is_northern_ireland = postcode and postcode.upper().startswith("BT") or False

    # Use override if set
    main_eori_num = office.eori_number or importer.eori_number

    # EORI numbers to return
    eori_numbers = [main_eori_num]

    if is_northern_ireland:
        eori_numbers.append(f"XI{main_eori_num[2:]}")

    return eori_numbers
