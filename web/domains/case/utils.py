from django.utils import timezone

from web.models.models import CaseReference
from web.utils.lock_manager import LockManager


# TODO: ICMSLST-752 write tests for this
def allocate_case_reference(
    *, lock_manager: LockManager, prefix: str, use_year: bool, min_digits: int
) -> str:
    """Allocate and return new case reference.

    NOTE: If case reference logic grows beyond this, consider a proper service
    layer."""

    lock_manager.ensure_tables_are_locked([CaseReference])

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

    new_ref_str = "%0*d" % (min_digits, new_ref)

    if use_year:
        return "/".join([prefix, str(year), new_ref_str])
    else:
        return "/".join([prefix, new_ref_str])
