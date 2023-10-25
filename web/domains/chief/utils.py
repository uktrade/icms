from django.core.cache import cache
from django.utils import timezone

from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import end_process_task
from web.mail.emails import send_completed_application_process_notifications
from web.models import ICMSHMRCChiefRequest, ImportApplication, Task, VariationRequest

from .types import ResponseError

HAWK_NONCE_EXPIRY = 60  # seconds
NONCE_CACHE_PREFIX = "hawk-nonce"


def seen_nonce(access_id: str, nonce: str, timestamp: str) -> bool:
    """True if this nonce has been used already."""
    key = f"{NONCE_CACHE_PREFIX}:{access_id}:{nonce}"
    # Returns True if the key/value was added, False if it already existed. So
    # we want to return False if the key/value was added, True if it existed.
    value_was_stored = cache.add(key, timestamp, timeout=HAWK_NONCE_EXPIRY)

    return not value_was_stored


def chief_licence_reply_approve_licence(application: ImportApplication) -> None:
    """Approve a licence that has been approved in CHIEF."""

    if application.status == ImpExpStatus.REVOKED:
        task = case_progress.get_expected_task(application, Task.TaskType.CHIEF_REVOKE_WAIT)
        end_process_task(task)
        return

    _finish_chief_wait_task(application)

    if application.status == ImportApplication.Statuses.VARIATION_REQUESTED:
        vr = application.variation_requests.get(status=VariationRequest.Statuses.OPEN)
        vr.status = VariationRequest.Statuses.ACCEPTED
        vr.save()

    application.status = ImportApplication.Statuses.COMPLETED
    application.save()

    document_pack.pack_draft_set_active(application)
    send_completed_application_process_notifications(application)


def chief_licence_reply_reject_licence(application: ImportApplication) -> None:
    """Reject a licence that has been rejected in CHIEF."""

    if application.status == ImpExpStatus.REVOKED:
        task = case_progress.get_expected_task(application, Task.TaskType.CHIEF_REVOKE_WAIT)
        end_process_task(task)
    else:
        task = _finish_chief_wait_task(application)

    Task.objects.create(process=application, task_type=Task.TaskType.CHIEF_ERROR, previous=task)


def _finish_chief_wait_task(application: ImportApplication) -> Task:
    case_progress.application_is_with_chief(application)
    task = case_progress.get_expected_task(application, Task.TaskType.CHIEF_WAIT)
    end_process_task(task)

    return task


def complete_chief_request(chief_req: ICMSHMRCChiefRequest) -> None:
    """Mark a ICMSHMRCChiefRequest record as complete."""

    chief_req.status = ICMSHMRCChiefRequest.CHIEFStatus.SUCCESS
    chief_req.response_received_datetime = timezone.now()
    chief_req.save()


def fail_chief_request(chief_req: ICMSHMRCChiefRequest, errors: list[ResponseError]) -> None:
    """Mark a ICMSHMRCChiefRequest record as a failure detailing the error code and message."""

    chief_req.status = ICMSHMRCChiefRequest.CHIEFStatus.ERROR
    chief_req.response_received_datetime = timezone.now()
    chief_req.save()

    for error in errors:
        chief_req.response_errors.create(error_code=error.error_code, error_msg=error.error_msg)
