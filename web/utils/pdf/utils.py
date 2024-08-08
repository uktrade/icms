import base64
import datetime as dt
import re
from collections.abc import Iterable
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode, urljoin

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from qrcode import QRCode

from web.domains.case._import.fa.types import FaImportApplication
from web.domains.case.services import document_pack
from web.domains.signature.utils import get_active_signature_file
from web.domains.template.utils import (
    fetch_cfs_declaration_translations,
    fetch_schedule_text,
    get_cover_letter_content,
    get_letter_fragment,
)
from web.flow.models import ProcessTypes
from web.models import SILGoodsSection582Obsolete  # /PS-IGNORE
from web.models import SILGoodsSection582Other  # /PS-IGNORE
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
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
    SILApplication,
    SILGoodsSection1,
    SILGoodsSection2,
    SILGoodsSection5,
    WoodQuotaApplication,
)
from web.sites import get_exporter_site_domain
from web.types import DocumentTypes
from web.utils import day_ordinal_date, is_northern_ireland_postcode, strip_spaces

if TYPE_CHECKING:
    from web.reports.serializers import GoodsSectionSerializer

Context = dict[str, Any]

SILGoods = (
    SILGoodsSection1
    | SILGoodsSection2
    | SILGoodsSection5
    | SILGoodsSection582Obsolete  # /PS-IGNORE
    | SILGoodsSection582Other  # /PS-IGNORE
)


def get_licence_context(
    application: ImportApplication, licence: ImportApplicationLicence, doc_type: DocumentTypes
) -> Context:
    importer = application.importer
    office = application.importer_office
    endorsements = get_licence_endorsements(application)
    signature, signature_file = get_active_signature_file()

    return {
        "process": application,
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
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
    }


def _get_fa_licence_context(
    application: FaImportApplication, licence: ImportApplicationLicence, doc_type: DocumentTypes
) -> Context:
    context = get_licence_context(application, licence, doc_type)

    return context | {
        "applicant_reference": application.applicant_reference,
        "issue_date": day_ordinal_date(timezone.now().date()),
        "paper_licence_only": licence.issue_paper_licence_only or False,
        "commodity_code": application.commodity_code,
    }


def get_fa_oil_licence_context(
    application: OpenIndividualLicenceApplication,
    licence: ImportApplicationLicence,
    doc_type: DocumentTypes,
) -> Context:
    context = _get_fa_licence_context(application, licence, doc_type)

    return context | {
        "consignment_country": "Any Country",
        "origin_country": "Any Country",
        "goods_description": application.goods_description(),
    }


def get_fa_dfl_licence_context(
    application: DFLApplication, licence: ImportApplicationLicence, doc_type: DocumentTypes
) -> Context:
    context = _get_fa_licence_context(application, licence, doc_type)

    return context | {
        "consignment_country": application.consignment_country.name,
        "origin_country": application.origin_country.name,
        "goods": _get_fa_dfl_goods(application),
    }


def get_fa_sil_licence_context(
    application: SILApplication,
    licence: ImportApplicationLicence,
    doc_type: DocumentTypes,
) -> Context:
    context = _get_fa_licence_context(application, licence, doc_type)
    markings_text = get_letter_fragment(application)

    return context | {
        "consignment_country": application.consignment_country.name,
        "origin_country": application.origin_country.name,
        "goods": _get_fa_sil_goods(application),
        "markings_text": markings_text,
    }


def get_country_and_geo_code(country: Country) -> str:
    return f"{country.name} {country.hmrc_code} {country.commission_code}"


def get_sanctions_goods_line(goods: SanctionsAndAdhocApplicationGoods) -> list[str]:
    goods_line = _split_text_field_newlines(goods.goods_description)
    last_line = goods_line.pop()
    quantity = f"{goods.quantity_amount:.3f}".rstrip("0").rstrip(".")
    value = f"{goods.value:.2f}".rstrip("0").rstrip(".")
    goods_line.append(f"{last_line}, {goods.commodity.commodity_code}, {quantity} kilos, {value}")
    return goods_line


def get_sanctions_licence_context(
    application: SanctionsAndAdhocApplication,
    licence: ImportApplicationLicence,
    doc_type: DocumentTypes,
) -> Context:
    context = get_licence_context(application, licence, doc_type)
    goods_list = [
        get_sanctions_goods_line(goods) for goods in application.sanctions_goods.order_by("pk")
    ]

    return context | {
        "country_of_manufacture": get_country_and_geo_code(application.origin_country),
        "country_of_shipment": get_country_and_geo_code(application.consignment_country),
        "ref": application.applicant_reference,
        "goods_list": goods_list,
        "sanctions_contact_email": settings.ICMS_SANCTIONS_EMAIL,
    }


def get_wood_licence_context(
    application: WoodQuotaApplication,
    licence: ImportApplicationLicence,
    doc_type: DocumentTypes,
) -> Context:
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


def get_cover_letter_context(application: FaImportApplication, doc_type: DocumentTypes) -> Context:
    content = get_cover_letter_content(application, doc_type)
    preview = doc_type == DocumentTypes.COVER_LETTER_PREVIEW
    signature, signature_file = get_active_signature_file()

    return {
        "content": content,
        "ilb_contact_address_split": settings.ILB_CONTACT_ADDRESS.split(", "),
        "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        "issue_date": timezone.now().date().strftime("%d %B %Y"),
        "page_title": "Cover Letter Preview",
        "preview": preview,
        "process": application,
        "signature": signature,
        "signature_file": signature_file,
    }


def get_licence_endorsements(application: ImportApplication) -> list[list[str]] | list[str]:
    """Return a list of endorsements for the application."""
    endorsements = [
        content.split("\n")
        for content in application.endorsements.values_list("content", flat=True)
    ]

    return endorsements


def _get_fa_dfl_goods(application: DFLApplication) -> list[str]:
    return [
        g.goods_description
        for g in application.goods_certificates.filter(is_active=True).order_by("created_datetime")
    ]


def _get_fa_sil_goods(application: SILApplication) -> Iterable[tuple[str, int | str]]:
    """Return all related FA SIL goods"""

    for g in application.goods_section1.filter(is_active=True):
        description = _get_description(g.description, "1")

        yield description, _get_unlimited_or_quantity(g)

    for g in application.goods_section2.filter(is_active=True):
        description = _get_description(g.description, "2")

        yield description, _get_unlimited_or_quantity(g)

    for g in application.goods_section5.filter(is_active=True):
        description = _get_description(g.description, g.section_5_clause.clause)

        yield description, _get_unlimited_or_quantity(g)

    for g in application.goods_legacy.filter(is_active=True):
        description = _get_description(g.description, "unknown")

        yield description, _get_unlimited_or_quantity(g)

    for g in application.goods_section582_obsoletes.filter(is_active=True):
        description = _get_description(
            f"{g.description} chambered in the obsolete calibre {g.obsolete_calibre}", "58(2)"
        )

        yield description, g.quantity

    for g in application.goods_section582_others.filter(is_active=True):
        description = _get_description(g.description, "58(2)")

        yield description, g.quantity


def _get_description(desc: str, section: str) -> str:
    return f"{desc} to which Section {section} of the Firearms Act 1968, as amended, applies."


def _get_unlimited_or_quantity(g: "SILGoods | GoodsSectionSerializer") -> str | int:
    return "Unlimited" if g.unlimited_quantity else g.quantity  # type:ignore[return-value]


def get_fa_sil_goods_item(
    goods_section: str,
    active_goods: Iterable["GoodsSectionSerializer"],
) -> list[tuple[str, str]]:
    """Used exclusively in web/reports/interfaces.py to load goods data."""

    goods = []

    for g in active_goods:
        match goods_section:
            #
            # Goods types with unlimited
            #
            case "goods_section1":
                description = _get_description(g.description, "1")
                quantity = _get_unlimited_or_quantity(g)

            case "goods_section2":
                description = _get_description(g.description, "2")
                quantity = _get_unlimited_or_quantity(g)

            case "goods_section5":
                description = _get_description(g.description, g.clause)  # type:ignore[arg-type]
                quantity = _get_unlimited_or_quantity(g)

            case "goods_legacy":
                description = _get_description(g.description, "unknown")
                quantity = _get_unlimited_or_quantity(g)

            #
            # Goods types without unlimited
            #
            case "goods_section582_others":
                description = _get_description(g.description, "58(2)")
                quantity = str(g.quantity)

            case "goods_section582_obsoletes":
                description = _get_description(
                    f"{g.description} chambered in the obsolete calibre {g.obsolete_calibre}",
                    "58(2)",
                )
                quantity = str(g.quantity)
            case _:
                raise ValueError(f"Unknown goods_section: {goods_section}")

        goods.append((description, str(quantity)))

    return goods


def _get_licence_start_date(licence: ImportApplicationLicence) -> str:
    if licence.licence_start_date:
        return day_ordinal_date(licence.licence_start_date)

    return "Licence Start Date not set"


def _get_licence_end_date(licence: ImportApplicationLicence) -> str:
    if licence.licence_end_date:
        return day_ordinal_date(licence.licence_end_date)

    return "Licence End Date not set"


def _get_licence_number(application: "ImportApplication", doc_type: DocumentTypes) -> str:
    if doc_type in (DocumentTypes.LICENCE_PRE_SIGN, DocumentTypes.LICENCE_SIGNED):
        doc_pack = document_pack.pack_latest_get(application)
        licence_doc = document_pack.doc_ref_licence_get(doc_pack)

        return licence_doc.reference

    return "[[Licence Number]]"


def _get_importer_eori_numbers(application: ImportApplication) -> list[str]:
    importer = application.importer
    office = application.importer_office
    postcode = office.postcode
    is_northern_ireland = is_northern_ireland_postcode(postcode)

    # Use override if set
    main_eori_num = office.eori_number or importer.eori_number

    # EORI numbers to return
    eori_numbers = [main_eori_num]

    # Add XI EORI for NI traders (only for firearm applications)
    if is_northern_ireland:
        # FA-OIL adds XI EORI for NI Traders
        if application.process_type == ProcessTypes.FA_OIL:
            eori_numbers.append(f"XI{main_eori_num[2:]}")

        # FA-SIL / FA-DFL check the consignment country as well
        elif (
            application.process_type in [ProcessTypes.FA_SIL, ProcessTypes.FA_DFL]
            and application.consignment_country in Country.util.get_eu_countries()
        ):
            eori_numbers.append(f"XI{main_eori_num[2:]}")

    return eori_numbers


def _certificate_document_context(
    application: "ExportApplication",
    certificate: "ExportApplicationCertificate",
    doc_type: DocumentTypes,
    country: Country,
) -> Context:
    qr_check_url = urljoin(get_exporter_site_domain(), reverse("checker:certificate-checker"))
    context: Context = {"qr_check_url": qr_check_url}

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
    country: Country,
) -> Context:
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
    country: Country,
) -> Context:
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
    country: Country,
) -> Context:
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
    country: Country,
) -> Context:
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
