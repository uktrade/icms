from random import randint
from typing import TYPE_CHECKING

from django.db.models import Manager, QuerySet
from django.utils import timezone

from web.domains.case.models import DocumentPackBase
from web.domains.case.services import reference
from web.domains.case.types import DocumentPack, ImpOrExp
from web.flow.models import ProcessTypes
from web.models import (
    CaseDocumentReference,
    Country,
    ExportApplication,
    ExportApplicationCertificate,
    ExportCertificateCaseDocumentReferenceData,
    ImportApplication,
    ImportApplicationLicence,
    User,
)

if TYPE_CHECKING:
    from web.utils.lock_manager import LockManager


PackStatus = DocumentPackBase.Status
DocumentType = CaseDocumentReference.Type

# Available service functions
__all__ = [
    #
    # document pack functions
    #
    "pack_draft_create",
    "pack_draft_get",
    "pack_draft_set_active",
    "pack_draft_archive",
    "pack_active_get",
    "pack_active_get_optional",
    "pack_active_revoke",
    "pack_revoked_get",
    "pack_latest_get",
    "pack_issued_get_all",
    "pack_workbasket_get_issued",
    "pack_workbasket_remove_pack",
    "pack_licence_history",
    "pack_certificate_history",
    #
    # doc_ref functions
    #
    "doc_ref_documents_create",
    "doc_ref_certificate_create",
    "doc_ref_certificate_get",
    "doc_ref_certificates_all",
    "doc_ref_licence_create",
    "doc_ref_licence_get",
    "doc_ref_licence_get_optional",
    "doc_ref_cover_letter_get",
    "doc_ref_documents_all",
    #
    # Types
    #
    "PackStatus",
    "DocumentType",
]


def pack_draft_create(application: ImpOrExp, *, variation_request: bool = False) -> DocumentPack:
    """Create a draft document pack for an import licence or export certificate.

    This is the main entry point to the service which all licences / certificates use.

    It is used in the following places:
        - Creating an import application.
        - Creating an export application.
        - A variation request is submitted for an import application.
        - A variation request is submitted for an export application.
        - A case is reopened after being withdrawn.
        - A case is reopened after being stopped.
        - Copying an existing export application.
    """

    if application.is_import_application():
        if variation_request:
            # Copy across the active licence values
            active_licence: ImportApplicationLicence = pack_active_get(application)
            kwargs = {
                "issue_paper_licence_only": active_licence.issue_paper_licence_only,
                "licence_start_date": active_licence.licence_start_date,
                "licence_end_date": active_licence.licence_end_date,
            }
        else:
            kwargs = {"issue_paper_licence_only": _get_paper_licence_only(application)}

        issued = application.licences.create(status=PackStatus.DRAFT, **kwargs)
    else:
        # a variation request doesn't change anything for export certificates.
        issued = application.certificates.create(status=PackStatus.DRAFT)

    return issued


def _get_paper_licence_only(application: ImportApplication) -> bool | None:
    """Get initial value for `issue_paper_licence_only` field.

    Some application types have a fixed value, others can choose it in the response
    preparation screen.
    """
    app_t = application.application_type

    # For when it is hardcoded True
    if app_t.paper_licence_flag and not app_t.electronic_licence_flag:
        return True

    # For when it is hardcoded False
    if app_t.electronic_licence_flag and not app_t.paper_licence_flag:
        return False

    # Specific check for FA_SIL applications
    # Default to "no" for everything other than a NI importer.
    if app_t.sub_type == app_t.SubTypes.SIL:
        if not application.importer_office.is_in_northern_ireland:
            return False

    # Default to None so the user can pick it later
    return None


def pack_draft_get(application: ImpOrExp) -> DocumentPack:
    """Get the current draft document pack."""

    return _get_qm(application).get(status=PackStatus.DRAFT)


def pack_draft_set_active(application: ImpOrExp) -> None:
    """Sets the latest draft licence to active and mark the previous active licence to archive."""

    draft_pack = pack_draft_get(application)
    active_pack = pack_active_get_optional(application)

    if active_pack:
        active_pack.status = PackStatus.ARCHIVED
        active_pack.save()

    draft_pack.case_completion_datetime = timezone.now()
    draft_pack.status = PackStatus.ACTIVE

    # Record the case_reference to see when viewing the application history
    draft_pack.case_reference = application.reference

    draft_pack.save()


def pack_draft_archive(application: ImpOrExp) -> None:
    """Archives the draft licence or certificate.

    This occurs when the following happens:
        - An application is refused by a caseworker.
        - A variation request is refused by a caseworker.
        - When an application is withdrawn.
        - When an application is stopped.
    """

    pack = pack_draft_get(application)
    pack.status = pack.Status.ARCHIVED
    pack.save()


def pack_active_get(application: ImpOrExp) -> DocumentPack:
    """Get the current active document pack."""

    return _get_qm(application).get(status=PackStatus.ACTIVE)


def pack_active_get_optional(application: ImpOrExp) -> DocumentPack | None:
    """Get the current active document pack returning None if there is no active pack."""

    packs = _get_qm(application).filter(status=PackStatus.ACTIVE)

    return packs.first()


def pack_active_revoke(application: ImpOrExp, reason: str, revoke_email_sent: bool) -> None:
    """Revoke the active document pack."""

    active_pack = pack_active_get(application)

    active_pack.status = PackStatus.REVOKED
    active_pack.revoke_reason = reason
    active_pack.revoke_email_sent = revoke_email_sent
    active_pack.save()


def pack_revoked_get(application: ImpOrExp) -> DocumentPack:
    """Get the revoked document pack."""

    return _get_qm(application).get(status=PackStatus.REVOKED)


def pack_latest_get(application: ImpOrExp) -> DocumentPack:
    """Return the most recent document pack.

    Only used in PDF code now.
    """

    packs = _get_qm(application)

    return packs.filter(status__in=[PackStatus.DRAFT, PackStatus.ACTIVE]).latest("created_at")


def pack_issued_get_all(application: ImpOrExp) -> QuerySet[DocumentPack]:
    """Return all completed document packs past and present."""

    packs = _get_qm(application)

    return packs.filter(
        status__in=[PackStatus.ACTIVE, PackStatus.ARCHIVED],
        # This filters refused applications that have no documents.
        case_completion_datetime__isnull=False,
    ).order_by("created_at")


def pack_workbasket_get_issued(application: ImpOrExp, user: User) -> QuerySet[DocumentPack]:
    """Return issued document packs to display in the workbasket for the given user."""

    packs = pack_issued_get_all(application)

    return packs.exclude(cleared_by=user).order_by("created_at")


def pack_workbasket_remove_pack(application: ImpOrExp, user: User, *, pack_pk: int) -> None:
    """Removes a document pack from displaying in the workbasket for the given user."""

    doc_packs = pack_issued_get_all(application)
    pack = doc_packs.select_for_update().get(pk=pack_pk)

    pack.cleared_by.add(user)


def pack_licence_history(application: ImportApplication) -> QuerySet[ImportApplicationLicence]:
    """Returns all document packs for an import application.

    Used in the case history page.
    """

    return _get_case_history(application)


def pack_certificate_history(
    application: ExportApplication,
) -> QuerySet[ExportApplicationCertificate]:
    """Returns all document packs for an export application.

    Used in the case history page.
    """

    return _get_case_history(application)


def _get_case_history(application: ImpOrExp) -> QuerySet[DocumentPack]:
    packs = _get_qm(application)

    return (
        packs.filter(case_reference__isnull=False)
        .prefetch_related("document_references")
        .order_by("-created_at")
    )


def doc_ref_documents_create(application: ImpOrExp, lock_manager: "LockManager") -> None:
    """Create the document references for the draft licence."""

    if application.is_import_application():
        licence_pack = pack_draft_get(application)

        if application.application_type.cover_letter_flag:
            licence_pack.document_references.get_or_create(document_type=DocumentType.COVER_LETTER)

        # Only call `get_import_licence_reference` if licence doc doesn't exist as it creates a record in UniqueReference.
        if not doc_ref_licence_get_optional(licence_pack):
            doc_ref = reference.get_import_licence_reference(
                lock_manager, application, licence_pack
            )
            doc_ref_licence_create(licence_pack, doc_ref)
    else:
        _create_export_documents(application, lock_manager)


def _create_export_documents(application: ExportApplication, lock_manager: "LockManager") -> None:
    """Creates document reference records for Export applications."""

    certificate = pack_draft_get(application)

    # Clear all document references as they may have changed
    doc_ref_documents_all(certificate).delete()

    if application.process_type in [ProcessTypes.COM, ProcessTypes.CFS, ProcessTypes.GMP]:
        app = application.get_specific_model()

        for country in app.countries.all().order_by("name"):
            doc_ref_certificate_create(
                certificate,
                reference.get_export_certificate_reference(lock_manager, app),
                country=country,
            )
    else:
        raise NotImplementedError(f"Unknown process_type: {application.process_type}")


def doc_ref_certificate_create(
    doc_pack: DocumentPack, doc_reference: str, *, country: Country
) -> CaseDocumentReference:
    """Create the certificate document reference"""

    if not doc_reference:
        raise ValueError("Unable to create a certificate without a document reference")

    cdr = _create_document(doc_pack, DocumentType.CERTIFICATE, doc_reference)

    ExportCertificateCaseDocumentReferenceData.objects.create(
        case_document_reference=cdr, country=country
    )

    return cdr


def doc_ref_certificate_get(
    doc_pack: ExportApplicationCertificate, country: Country
) -> CaseDocumentReference:
    """Get the certificate document reference"""

    certificates = doc_ref_certificates_all(doc_pack)

    kwargs = {"reference_data__country": country}

    return certificates.get(**kwargs)


def doc_ref_certificates_all(
    doc_pack: ExportApplicationCertificate,
) -> QuerySet[CaseDocumentReference]:
    """Get all certificate document references."""

    documents = doc_ref_documents_all(doc_pack)

    return documents.filter(document_type=DocumentType.CERTIFICATE)


def doc_ref_licence_create(doc_pack: DocumentPack, doc_reference: str) -> CaseDocumentReference:
    """Create the licence document reference"""

    if not doc_reference:
        raise ValueError("Unable to create a licence without a document reference")

    return _create_document(doc_pack, DocumentType.LICENCE, doc_reference)


def doc_ref_licence_get(doc_pack: ImportApplicationLicence) -> CaseDocumentReference:
    """Get the licence document reference"""

    documents = doc_ref_documents_all(doc_pack)
    licence = documents.get(document_type=DocumentType.LICENCE)

    return licence


def doc_ref_licence_get_optional(
    doc_pack: ImportApplicationLicence,
) -> CaseDocumentReference | None:
    """Return the licence document returning None if there is no licence document."""

    documents = doc_ref_documents_all(doc_pack)
    licence_qs = documents.filter(document_type=DocumentType.LICENCE)

    return licence_qs.first()


def doc_ref_cover_letter_get(doc_pack: ImportApplicationLicence) -> CaseDocumentReference:
    """Get the cover letter document reference."""

    documents = doc_ref_documents_all(doc_pack)

    return documents.get(document_type=DocumentType.COVER_LETTER)


def doc_ref_documents_all(doc_pack: DocumentPack) -> QuerySet[CaseDocumentReference]:
    """Get all document references."""

    return doc_pack.document_references.order_by("pk")


def _create_document(
    doc_pack: DocumentPack, doc_type: str, doc_reference: str | None = None
) -> CaseDocumentReference:
    # TODO ICMSLST-2406 check_code generation is currently mimicing how V1 works
    check_code = randint(10000000, 99999999)
    return doc_pack.document_references.create(
        document_type=doc_type, reference=doc_reference, check_code=str(check_code)
    )


def _get_qm(application: ImpOrExp) -> Manager[DocumentPack]:
    if application.is_import_application():
        return application.licences
    else:
        return application.certificates
