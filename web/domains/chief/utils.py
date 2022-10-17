from django.utils import timezone

from web.domains.case._import.models import ImportApplication, LiteHMRCChiefRequest
from web.domains.case.models import VariationRequest
from web.domains.case.utils import (
    get_application_current_task,
    set_application_licence_or_certificate_active,
)
from web.flow.models import Task

from .types import ResponseError


def chief_licence_reply_approve_licence(application: ImportApplication) -> None:
    """Approve a licence that has been approved in CHIEF."""

    _finish_chief_wait_task(application)

    if application.status == ImportApplication.Statuses.VARIATION_REQUESTED:
        vr = application.variation_requests.get(status=VariationRequest.OPEN)
        vr.status = VariationRequest.ACCEPTED
        vr.save()

    application.status = ImportApplication.Statuses.COMPLETED
    application.save()

    set_application_licence_or_certificate_active(application)


def chief_licence_reply_reject_licence(application: ImportApplication) -> None:
    """Reject a licence that has been rejected in CHIEF."""

    task = _finish_chief_wait_task(application)

    Task.objects.create(process=application, task_type=Task.TaskType.CHIEF_ERROR, previous=task)


def _finish_chief_wait_task(application: ImportApplication) -> Task:
    task = get_application_current_task(application, "import", Task.TaskType.CHIEF_WAIT)
    task.is_active = False
    task.finished = timezone.now()
    task.save()

    return task


def complete_chief_request(chief_req: LiteHMRCChiefRequest) -> None:
    """Mark a LiteHMRCChiefRequest record as complete."""

    chief_req.status = LiteHMRCChiefRequest.CHIEFStatus.SUCCESS
    chief_req.response_received_datetime = timezone.now()
    chief_req.save()


def fail_chief_request(chief_req: LiteHMRCChiefRequest, errors: list[ResponseError]) -> None:
    """Mark a LiteHMRCChiefRequest record as a failure detailing the error code and message."""

    chief_req.status = LiteHMRCChiefRequest.CHIEFStatus.ERROR
    chief_req.response_received_datetime = timezone.now()
    chief_req.save()

    for error in errors:
        chief_req.response_errors.create(error_code=error.error_code, error_msg=error.error_msg)
