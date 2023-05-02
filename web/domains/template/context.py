from typing import Protocol

from django.conf import settings

from web.domains.case.services import document_pack
from web.flow.models import ProcessTypes
from web.models import AccessRequest, ExportApplication, ImportApplication, Process
from web.types import DocumentTypes


class TemplateContextProcessor(Protocol):
    def __init__(self, process: Process, *args, **kwargs):
        ...

    def __getitem__(self, item: str) -> str:
        ...


class CoverLetterTemplateContext:
    date_fmt = "%d %B %Y"

    valid_placeholders: list[str] = [
        "APPLICATION_SUBMITTED_DATE",
        "CONTACT_NAME",
        "COUNTRY_OF_CONSIGNMENT",
        "COUNTRY_OF_ORIGIN",
        "LICENCE_END_DATE",
        "LICENCE_NUMBER",
    ]

    def __init__(self, process: ImportApplication, document_type: DocumentTypes) -> None:
        self.application = process
        self.document_type = document_type

    def _placeholder(self, item: str) -> str:
        return f'<span class="placeholder">[[{item}]]</span>'

    def _context(self, item: str) -> str:
        match item:
            case "APPLICATION_SUBMITTED_DATE":
                return self.application.submit_datetime.strftime(self.date_fmt)
            case "CONTACT_NAME":
                return self.application.contact.full_name
            case "COUNTRY_OF_CONSIGNMENT":
                return self.application.consignment_country.name
            case "COUNTRY_OF_ORIGIN":
                return self.application.origin_country.name
            case _:
                raise ValueError(f"{item} is not a valid cover letter template context value")

    def _preview_context(self, item: str) -> str:
        match item:
            case "LICENCE_NUMBER":
                return self._placeholder(item)
            case "LICENCE_END_DATE":
                return self._placeholder(item)
        return self._context(item)

    def _full_context(self, item: str) -> str:
        licence = document_pack.pack_draft_get(self.application)

        match item:
            case "LICENCE_NUMBER":
                return document_pack.doc_ref_licence_get(licence).reference
            case "LICENCE_END_DATE":
                return licence.licence_end_date.strftime(self.date_fmt)
        return self._context(item)

    def __getitem__(self, item: str) -> str:
        match self.document_type:
            case DocumentTypes.COVER_LETTER_PREVIEW:
                return self._preview_context(item)
            case DocumentTypes.COVER_LETTER_PRE_SIGN:
                return self._full_context(item)
            case DocumentTypes.COVER_LETTER_SIGNED:
                return self._full_context(item)
            case _:
                raise ValueError(f"{self.document_type} is not a valid document type")


class EmailTemplateContext:
    def __init__(self, process: Process) -> None:
        self.process = process

    def __getitem__(self, item: str) -> str:
        match self.process:
            case ImportApplication():
                return self._import_context(item)
            case ExportApplication():
                return self._export_context(item)
            case AccessRequest():
                return self._access_context(item)
            case _:
                raise ValueError(
                    "Process must be an instance of ImportApplication /"
                    " ExportApplication / AccessRequest"
                )

    def _application_context(self, item: str) -> str:
        match item:
            case "APPLICATION_TYPE":
                return self.process.PROCESS_TYPE.label
            case "CASE_OFFICER_EMAIL":
                return settings.ILB_CONTACT_EMAIL
            case "CASE_OFFICER_NAME":
                return self.process.case_owner.full_name
            case "CASE_OFFICER_PHONE":
                return settings.ILB_CONTACT_PHONE
            case "CASE_REFERENCE":
                return self.process.reference
        return self._context(item)

    def _import_context(self, item: str) -> str:
        match item:
            case "LICENCE_NUMBER":
                pack = document_pack.pack_active_get(self.process)
                return document_pack.doc_ref_licence_get(pack).reference
        return self._application_context(item)

    def _export_context(self, item: str) -> str:
        match item:
            case "CERTIFICATE_REFERENCES":
                pack = document_pack.pack_active_get(self.process)
                certificates = document_pack.doc_ref_certificates_all(pack)
                return ", ".join(certificates.values_list("reference", flat=True))
            case "EXPORTER_ADDRESS":
                return str(self.process.exporter_office)
            case "EXPORTER_NAME":
                return str(self.process.exporter)

        match self.process.process_type:
            case ProcessTypes.GMP:
                return self._gmp_app_context(item)

        return self._application_context(item)

    def _access_context(self, item: str) -> str:
        return self._context(item)

    def _gmp_app_context(self, item: str) -> str:
        match item:
            case "MANUFACTURER_NAME":
                return self.process.manufacturer_name
            case "MANUFACTURER_ADDRESS":
                return self.process.manufacturer_address
            case "MANUFACTURER_POSTCODE":
                return self.process.manufacturer_postcode
            case "RESPONSIBLE_PERSON_ADDRESS":
                return self.process.responsible_person_address
            case "RESPONSIBLE_PERSON_NAME":
                return self.process.responsible_person_name
            case "RESPONSIBLE_PERSON_POSTCODE":
                return self.process.responsible_person_postcode
            case "BRAND_NAMES":
                return ", ".join(self.process.brands.values_list("brand_name", flat=True))

        return self._application_context(item)

    def _context(self, item: str) -> str:
        match item:
            case _:
                raise ValueError(f"{item} is not a valid email template context value")


class RevokedEmailTemplateContext(EmailTemplateContext):
    def _import_context(self, item: str) -> str:
        match item:
            case "LICENCE_NUMBER":
                pack = document_pack.pack_revoked_get(self.process)
                return document_pack.doc_ref_licence_get(pack).reference
        return super()._import_context(item)

    def _export_context(self, item: str) -> str:
        match item:
            case "CERTIFICATE_REFERENCES":
                pack = document_pack.pack_revoked_get(self.process)
                certificates = document_pack.doc_ref_certificates_all(pack)
                return ", ".join(certificates.values_list("reference", flat=True))
        return super()._export_context(item)
