import base64
import datetime as dt
import re
from collections.abc import Collection
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Union
from urllib.parse import urlencode, urljoin

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from qrcode import QRCode

from web.domains.case.services import document_pack
from web.domains.signature.utils import get_active_signature_file
from web.domains.template.utils import (
    ScheduleText,
    fetch_cfs_declaration_translations,
    fetch_schedule_text,
    get_cover_letter_content,
    get_letter_fragment,
)
from web.models import CertificateOfGoodManufacturingPracticeApplication
from web.sites import get_exporter_site_domain
from web.types import DocumentTypes
from web.utils import day_ordinal_date, strip_spaces

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.domains.case._import.fa.types import FaImportApplication
    from web.domains.case._import.fa_sil import models as sil_models
    from web.domains.case.types import ImpOrExp
    from web.models import (
        CertificateOfFreeSaleApplication,
        CertificateOfManufactureApplication,
        Country,
        DFLApplication,
        ExportApplication,
        ExportApplicationCertificate,
        ImportApplication,
        ImportApplicationLicence,
        OpenIndividualLicenceApplication,
        SanctionsAndAdhocApplication,
        SanctionsAndAdhocApplicationGoods,
        WoodQuotaApplication,
    )

    SILGoods = Union[
        sil_models.SILGoodsSection1,
        sil_models.SILGoodsSection2,
        sil_models.SILGoodsSection5,
        sil_models.SILGoodsSection582Obsolete,  # /PS-IGNORE
        sil_models.SILGoodsSection582Other,  # /PS-IGNORE
    ]

    Context = dict[str, str | bool | Collection[str] | ImpOrExp | dict[int, ScheduleText]]


def get_licence_context(
    application: "ImpOrExp", licence: "ImportApplicationLicence", doc_type: DocumentTypes
) -> "Context":
    importer = application.importer
    office = application.importer_office
    endorsements = get_licence_endorsements(application)
    signature, signature_file = get_active_signature_file()

    return {
        "process": application,
        "page_title": "Licence Preview",
        "preview_licence": doc_type == DocumentTypes.LICENCE_PREVIEW,
        "importer_name": importer.display_name,
        "eori_numbers": _get_importer_eori_numbers(application),
        "importer_address": office.address.split("\n"),
        "importer_postcode": office.postcode,
        "endorsements": endorsements,
        "licence_number": _get_licence_number(application, doc_type),
        "licence_start_date": _get_licence_start_date(licence),
        "licence_end_date": _get_licence_end_date(licence),
        "signature": signature,
        "signature_file": signature_file,
    }


def _get_fa_licence_context(
    application: "FaImportApplication", licence: "ImportApplicationLicence", doc_type: DocumentTypes
) -> "Context":
    context = get_licence_context(application, licence, doc_type)

    return context | {
        "applicant_reference": application.applicant_reference,
        "issue_date": day_ordinal_date(timezone.now().date()),
        "paper_licence_only": licence.issue_paper_licence_only or False,
    }


def get_fa_oil_licence_context(
    application: "OpenIndividualLicenceApplication",
    licence: "ImportApplicationLicence",
    doc_type: DocumentTypes,
) -> "Context":
    context = _get_fa_licence_context(application, licence, doc_type)

    return context | {
        "consignment_country": "Any Country",
        "origin_country": "Any Country",
        "goods_description": application.goods_description(),
    }


def get_fa_dfl_licence_context(
    application: "DFLApplication", licence: "ImportApplicationLicence", doc_type: DocumentTypes
) -> "Context":
    context = _get_fa_licence_context(application, licence, doc_type)

    return context | {
        "consignment_country": application.consignment_country.name,
        "origin_country": application.origin_country.name,
        "goods": _get_fa_dfl_goods(application),
    }


def get_fa_sil_licence_context(
    application: "sil_models.SILApplication",
    licence: "ImportApplicationLicence",
    doc_type: DocumentTypes,
) -> "Context":
    context = _get_fa_licence_context(application, licence, doc_type)
    markings_text = get_letter_fragment(application)

    return context | {
        "consignment_country": application.consignment_country.name,
        "origin_country": application.origin_country.name,
        "goods": _get_fa_sil_goods(application),
        "markings_text": markings_text,
    }


def get_country_and_geo_code(country: "Country") -> str:
    return f"{country.name} {country.hmrc_code} {country.commission_code}"


def get_sanctions_goods_line(goods: "SanctionsAndAdhocApplicationGoods") -> list[str]:
    goods_line = _split_text_field_newlines(goods.goods_description)
    last_line = goods_line.pop()
    quantity = f"{goods.quantity_amount:.3f}".rstrip("0").rstrip(".")
    value = f"{goods.value:.2f}".rstrip("0").rstrip(".")
    goods_line.append(f"{last_line}, {goods.commodity.commodity_code}, {quantity} kilos, {value}")
    return goods_line


def get_sanctions_licence_context(
    application: "SanctionsAndAdhocApplication",
    licence: "ImportApplicationLicence",
    doc_type: DocumentTypes,
) -> "Context":
    context = get_licence_context(application, licence, doc_type)
    goods_list = [
        get_sanctions_goods_line(goods) for goods in application.sanctions_goods.order_by("pk")
    ]

    return context | {
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "country_of_manufacture": get_country_and_geo_code(application.origin_country),
        "country_of_shipment": get_country_and_geo_code(application.consignment_country),
        "ref": application.applicant_reference,
        "goods_list": goods_list,
    }


def get_wood_licence_context(
    application: "WoodQuotaApplication",
    licence: "ImportApplicationLicence",
    doc_type: DocumentTypes,
) -> "Context":
    context = get_licence_context(application, licence, doc_type)

    return context | {
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "ref": application.applicant_reference,
        "goods": application.goods_description,
        "commodity_code": application.commodity.commodity_code,
        "quantity": f"{application.goods_qty:.2f}".rstrip("0").rstrip("."),
        "exporter_name": application.exporter_name,
        "exporter_address": _split_text_field_newlines(application.exporter_address),
        "exporter_vat_number": application.exporter_vat_nr,
    }


def get_cover_letter_context(
    application: "FaImportApplication", doc_type: DocumentTypes
) -> "Context":
    content = get_cover_letter_content(application, doc_type)
    preview = doc_type == DocumentTypes.COVER_LETTER_PREVIEW

    return {
        "content": content,
        "ilb_contact_address_split": settings.ILB_CONTACT_ADDRESS.split(", "),
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "issue_date": timezone.now().date().strftime("%d %B %Y"),
        "page_title": "Cover Letter Preview",
        "preview": preview,
        "process": application,
    }


# TODO: ICMSLST-1428 Revisit this - See nl2br
#       Add proper test for this function
def get_licence_endorsements(application: "ImpOrExp") -> list[str]:
    endorsements = [
        content.split("\r\n")
        for content in application.endorsements.values_list("content", flat=True)
    ]

    return endorsements


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
    if goods_section in ["goods_section1", "goods_section2", "goods_section5"]:
        goods = []
        for g in active_goods:
            quantity = "Unlimited" if g.unlimited_quantity else g.quantity
            goods.append((f"{g.description} {label_suffix}", quantity))

        return goods

    elif goods_section == "goods_section582_others":
        return [(f"{g.description} {label_suffix}", g.quantity) for g in active_goods]

    elif goods_section == "goods_section582_obsoletes":
        return [
            (
                f"{g.description} chambered in the obsolete calibre {g.obsolete_calibre} {label_suffix}",
                g.quantity,
            )
            for g in active_goods
        ]

    return []


def _get_licence_start_date(licence: "ImportApplicationLicence") -> str:
    if licence.licence_start_date:
        return day_ordinal_date(licence.licence_start_date)

    return "Licence Start Date not set"


def _get_licence_end_date(licence: "ImportApplicationLicence") -> str:
    if licence.licence_end_date:
        return day_ordinal_date(licence.licence_end_date)

    return "Licence End Date not set"


def _get_licence_number(application: "ImportApplication", doc_type: DocumentTypes) -> str:
    # TODO: ICMSLST-697 Revisit when signing the document (it may need its own context / template)
    if doc_type in (DocumentTypes.LICENCE_PRE_SIGN, DocumentTypes.LICENCE_SIGNED):
        doc_pack = document_pack.pack_latest_get(application)
        licence_doc = document_pack.doc_ref_licence_get(doc_pack)

        return licence_doc.reference

    return "[[Licence Number]]"


def _get_importer_eori_numbers(application: "FaImportApplication") -> list[str]:
    # TODO: ICMSLST-580 Revisit the EORI numbers that appear on a licence.
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


def _certificate_document_context(
    application: "ExportApplication",
    certificate: "ExportApplicationCertificate",
    doc_type: DocumentTypes,
    country: "Country",
) -> "Context":
    qr_check_url = urljoin(get_exporter_site_domain(), reverse("checker:certificate-checker"))
    context: "Context" = {"qr_check_url": qr_check_url}

    if doc_type == DocumentTypes.CERTIFICATE_PREVIEW:
        context["reference"] = "[[CERTIFICATE_REFERENCE]]"
        return context

    document = document_pack.doc_ref_certificate_get(certificate, country)
    reference = document.reference

    query_params = {
        "CERTIFICATE_REFERENCE": reference,
        "CERTIFICATE_CODE": document.check_code,
        "COUNTRY": document.reference_data.country.id,
        "ORGANSIATION": application.exporter.name,
    }
    qr = QRCode(border=0, box_size=10)
    qr.add_data(qr_check_url + "?" + urlencode(query_params))
    qr_image = qr.make_image()
    tmpfile = NamedTemporaryFile(delete=True)
    qr_image.save(tmpfile.name)
    qr_img = base64.b64encode(tmpfile.read())  # /PS-IGNORE

    return context | {
        "certificate_code": document.check_code,
        "qr_img_base64": qr_img.decode("utf8"),
        "reference": reference,
    }


def _get_certificate_context(
    application: "ExportApplication",
    certificate: "ExportApplicationCertificate",
    doc_type: DocumentTypes,
    country: "Country",
) -> "Context":
    context = _certificate_document_context(application, certificate, doc_type, country)
    preview = doc_type == DocumentTypes.CERTIFICATE_PREVIEW
    signature, signature_file = get_active_signature_file()
    if certificate.case_completion_datetime:
        issue_date = day_ordinal_date(certificate.case_completion_datetime.date())
    else:
        issue_date = day_ordinal_date(dt.datetime.now().date())

    return context | {
        "exporter_name": application.exporter.name.upper(),
        "exporter_address": str(application.exporter_office).upper(),
        "country": country.name,
        "issue_date": issue_date,
        "process": application,
        "preview": preview,
        "signature": signature,
        "signature_file": signature_file,
    }


def get_cfs_certificate_context(
    application: "CertificateOfFreeSaleApplication",
    certificate: "ExportApplicationCertificate",
    doc_type: DocumentTypes,
    country: "Country",
) -> "Context":
    context = _get_certificate_context(application, certificate, doc_type, country)

    context |= {
        "schedule_text": fetch_schedule_text(application, country),
        "statement_translations": fetch_cfs_declaration_translations(country),
        "page_title": f"Certificate of Free Sale ({country.name}) Preview",
    }

    return context


def get_com_certificate_context(
    application: "CertificateOfManufactureApplication",
    certificate: "ExportApplicationCertificate",
    doc_type: DocumentTypes,
    country: "Country",
) -> "Context":
    context = _get_certificate_context(application, certificate, doc_type, country)
    return context | {
        "page_title": f"Certificate of Manufacture ({country.name}) Preview",
        "product_name": application.product_name,
        "chemical_name": application.chemical_name,
        "manufacturing_process_list": _split_text_field_newlines(application.manufacturing_process),
    }


def get_gmp_certificate_context(
    application: "CertificateOfGoodManufacturingPracticeApplication",
    certificate: "ExportApplicationCertificate",
    doc_type: DocumentTypes,
    country: "Country",
) -> "Context":
    context = _get_certificate_context(application, certificate, doc_type, country)
    expiry_delta = relativedelta(years=3)

    if certificate.case_completion_datetime:
        expiry_date = certificate.case_completion_datetime.date() + expiry_delta
    else:
        expiry_date = dt.datetime.now().date() + expiry_delta

    ni_country_type = CertificateOfGoodManufacturingPracticeApplication.CountryType.NIR

    return context | {
        "page_title": f"Certificate of Good Manufacturing Practice ({country.name}) Preview",
        "brand_name": application.brand_name,
        "manufacturer_name": application.manufacturer_name,
        "manufacturer_address": strip_spaces(
            application.manufacturer_address, application.manufacturer_postcode
        ),
        "manufacturer_country": application.manufacturer_country,
        "expiry_date": day_ordinal_date(expiry_date),
        "is_ni": application.manufacturer_country == ni_country_type,
    }


def _split_text_field_newlines(text: str) -> list[str]:
    """Splits a text field separated by newlines into a list of strings

    e.g. "a\nb\n\n\nc\n" ->  ["a", "b", "c"]"""
    cleaned = re.sub(r"\n+", "\n", text.strip())

    return [line.strip() for line in cleaned.split("\n") if line.strip()]


def cfs_cover_letter_key_filename() -> tuple[str, str]:
    static_files_s3_prefix = "static_documents"
    cfs_cover_letter_filename = "CFS Letter"
    filename = f"{cfs_cover_letter_filename}.pdf"
    key = f"{static_files_s3_prefix}/{filename}"
    return key, filename
