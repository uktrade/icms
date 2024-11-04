from typing import TYPE_CHECKING, Literal

from django.utils import timezone

from web.flow.models import ProcessTypes
from web.models import UniqueReference

if TYPE_CHECKING:
    from web.domains.case.types import ImpOrExp
    from web.models import (
        ExportApplication,
        ImportApplication,
        ImportApplicationLicence,
    )
    from web.utils.lock_manager import LockManager

Prefix = UniqueReference.Prefix


def get_application_case_reference(lock_manager: "LockManager", application: "ImpOrExp") -> str:
    """Retrieve an application case reference for import & export applications"""

    if application.is_import_application():
        prefix = Prefix.IMPORT_APP
    else:
        if application.process_type == ProcessTypes.GMP:
            prefix = Prefix.EXPORT_APP_GA
        else:
            prefix = Prefix.EXPORT_APP_CA

    use_year = True
    case_reference = _get_next_reference(lock_manager, prefix=prefix, use_year=use_year)

    return _get_reference_string(case_reference, use_year=use_year, min_digits=5)


def get_variation_request_case_reference(application: "ImpOrExp") -> str:
    """Get the case reference updated with the count of variations associated with the application."""
    ref = application.get_reference()

    if ref == application.DEFAULT_REF:
        raise ValueError("Application has not been assigned yet.")

    variations = application.variation_requests.all()

    if not application.is_import_application():
        # Can't import VariationRequest due to circular dependency
        # Should use VariationRequest.Statuses.OPEN & VariationRequest.Statuses.CLOSED
        variations = variations.filter(status__in=["OPEN", "CLOSED"])

    # e.g [prefix, year, reference]
    case_ref_sections = ref.split("/")[:3]
    variation_count = variations.count()

    if variation_count:
        # e.g. [prefix, year, reference, variation_count]
        case_ref_sections.append(str(variation_count))

    # Return the new joined up case reference
    return "/".join(case_ref_sections)


def get_import_licence_reference(
    lock_manager: "LockManager",
    application: "ImportApplication",
    licence: "ImportApplicationLicence",
) -> str:
    """Get the licence reference for the supplied import application"""

    if not application.licence_reference:
        application.licence_reference = _get_next_reference(
            lock_manager, prefix=Prefix.IMPORT_LICENCE_DOCUMENT, use_year=False
        )
        application.save()

    licence_type = "paper" if licence.issue_paper_licence_only else "electronic"

    return _get_licence_reference(
        licence_type, application.process_type, application.licence_reference.reference  # type: ignore[arg-type]
    )


def get_export_certificate_reference(
    lock_manager: "LockManager", application: "ExportApplication"
) -> str:
    """Creates an export application certificate reference.

    Reference formats:
        - XXX/YYYY/NNNNN

    Reference breakdown:
        - XXX: certificate category
        - YYYY: year certificate issued
        - NNNNN: Next sequence value (padded to 5 digits)
    """

    match application.process_type:
        case ProcessTypes.CFS:
            prefix = Prefix.EXPORT_CERTIFICATE_DOCUMENT_CFS
        case ProcessTypes.COM:
            prefix = Prefix.EXPORT_CERTIFICATE_DOCUMENT_COM
        case ProcessTypes.GMP:
            prefix = Prefix.EXPORT_CERTIFICATE_DOCUMENT_GMP
        case _:
            raise ValueError(
                f"Invalid process_type {application.process_type}: ExportApplication process_type is required."
            )

    case_reference = _get_next_reference(lock_manager, prefix=prefix, use_year=True)

    return _get_reference_string(case_reference, use_year=True, min_digits=5)


def get_mailshot_reference(lock_manager: "LockManager") -> str:
    """Get next mailshot reference"""
    use_year = False
    case_reference = _get_next_reference(lock_manager, prefix=Prefix.MAILSHOT, use_year=use_year)

    return _get_reference_string(case_reference, use_year=use_year, min_digits=1)


def get_importer_access_request_reference(lock_manager: "LockManager") -> str:
    use_year = False
    case_reference = _get_next_reference(
        lock_manager, prefix=Prefix.IMP_ACCESS_REQ, use_year=use_year
    )

    return _get_reference_string(case_reference, use_year=use_year, min_digits=1)


def get_exporter_access_request_reference(lock_manager: "LockManager") -> str:
    use_year = False
    case_reference = _get_next_reference(
        lock_manager, prefix=Prefix.EXP_ACCESS_REQ, use_year=use_year
    )

    return _get_reference_string(case_reference, use_year=use_year, min_digits=1)


def _get_next_reference(
    lock_manager: "LockManager", *, prefix: str, use_year: bool
) -> UniqueReference:
    """Return the next available UniqueReference instance."""

    lock_manager.ensure_tables_are_locked([UniqueReference])

    year: int | None

    if use_year:
        year = timezone.now().year
    else:
        year = None

    last_ref = UniqueReference.objects.filter(prefix=prefix, year=year).order_by("reference").last()

    if last_ref:
        new_ref = last_ref.reference + 1
    else:
        new_ref = 1

    case_reference = UniqueReference.objects.create(prefix=prefix, year=year, reference=new_ref)

    return case_reference


def _get_reference_string(case_reference: UniqueReference, use_year: bool, min_digits: int) -> str:
    new_ref_str = f"{case_reference.reference:0{min_digits}}"

    if use_year:
        return "/".join([case_reference.prefix, str(case_reference.year), new_ref_str])
    else:
        return "/".join([case_reference.prefix, new_ref_str])


def _get_licence_reference(
    licence_type: Literal["electronic", "paper"],
    process_type: str,
    next_sequence_value: int,
) -> str:
    """Get an import application licence reference.

    Reference formats:
        - Electronic licence: GBxxxNNNNNNNa
        - Paper licence: NNNNNNNa

    Reference breakdown:
        - GB: reference prefix
        - xxx: licence category
        - NNNNNNN: Next sequence value (padded to 7 digits)
        - a: check digit

    :param licence_type: Type of licence reference to create
    :param process_type: ProcessTypes value
    :param next_sequence_value: Number representing the next available sequence number.
    """

    check_digit = _get_check_digit(next_sequence_value)
    sequence_and_check_digit = f"{next_sequence_value:07}{check_digit}"

    if licence_type == "electronic":
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

        return f"GB{xxx}{sequence_and_check_digit}"

    return sequence_and_check_digit


def _get_check_digit(val: int) -> str:
    idx = val % 13
    return "ABCDEFGHXJKLM"[idx]
