from typing import TYPE_CHECKING, Optional

from django.utils import timezone

from web.flow.models import ProcessTypes
from web.models.models import CaseReference

if TYPE_CHECKING:
    from web.domains.case.types import ImpOrExp
    from web.utils.lock_manager import LockManager


def get_application_case_reference(lock_manager: "LockManager", application: "ImpOrExp"):
    """Retrieve an application case reference for import & export applications"""

    if application.is_import_application():
        prefix = "IMA"
    else:
        if application.process_type == ProcessTypes.GMP:
            prefix = "GA"
        else:
            prefix = "CA"

    return get_next_reference(lock_manager, prefix=prefix, use_year=True, min_digits=5)


def get_mailshot_reference(lock_manager: "LockManager"):
    """Get next mailshot reference"""
    return get_next_reference(lock_manager, prefix="MAIL", use_year=False, min_digits=1)


def get_importer_access_request_reference(lock_manager: "LockManager"):
    return get_next_reference(lock_manager, prefix="IAR", use_year=False, min_digits=1)


def get_exporter_access_request_reference(lock_manager: "LockManager"):
    return get_next_reference(lock_manager, prefix="EAR", use_year=False, min_digits=1)


def get_next_reference(
    lock_manager: "LockManager", *, prefix: str, use_year: bool, min_digits: int
) -> str:
    """Return the next available reference value."""

    lock_manager.ensure_tables_are_locked([CaseReference])

    year: Optional[int]

    if use_year:
        year = timezone.now().year
    else:
        year = None

    last_ref = CaseReference.objects.filter(prefix=prefix, year=year).order_by("reference").last()

    if last_ref:
        new_ref = last_ref.reference + 1
    else:
        new_ref = 1

    CaseReference.objects.create(prefix=prefix, year=year, reference=new_ref)

    new_ref_str = f"{new_ref:0{min_digits}}"

    if use_year:
        return "/".join([prefix, str(year), new_ref_str])
    else:
        return "/".join([prefix, new_ref_str])
