import datetime
from typing import Any, Literal, Optional

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone

from web.domains.case._import.models import ImportApplication
from web.domains.case.export.models import ExportApplication
from web.domains.file.models import File
from web.domains.user.models import User
from web.flow.models import ProcessTypes, Task
from web.utils.s3 import get_file_from_s3

from .models import VariationRequest
from .shared import ImpExpStatus
from .types import ImpOrExp, ImpOrExpOrAccess


def get_variation_request_case_reference(application: ImpOrExp) -> str:
    """Get the case reference updated with the count of variations associated with the application."""

    ref = application.get_reference()

    if ref == application.DEFAULT_REF:
        raise ValueError("Application has not been assigned yet.")

    variations = application.variation_requests.all()

    if not application.is_import_application():
        variations = variations.filter(status__in=[VariationRequest.OPEN, VariationRequest.CLOSED])

    # e.g [prefix, year, reference]
    case_ref_sections = ref.split("/")[:3]
    variation_count = variations.count()

    if variation_count:
        # e.g. [prefix, year, reference, variation_count]
        case_ref_sections.append(str(variation_count))

    # Return the new joined up case reference
    return "/".join(case_ref_sections)


def check_application_permission(application: ImpOrExpOrAccess, user: User, case_type: str) -> None:
    """Check the given user has permission to access the given application."""

    if user.has_perm("web.ilb_admin"):
        return

    if case_type == "access":
        if user != application.submitted_by:
            raise PermissionDenied

    elif case_type in ["import", "export"]:
        assert isinstance(application, (ImportApplication, ExportApplication))

        if not _has_importer_exporter_access(user, case_type):
            raise PermissionDenied

        is_contact = application.user_is_contact_of_org(user)
        is_agent = application.user_is_agent_of_org(user)

        if not is_contact and not is_agent:
            raise PermissionDenied

    else:
        # Should never get here.
        raise PermissionDenied


def get_application_current_task(
    application: ImpOrExpOrAccess, case_type: str, task_type: str, select_for_update: bool = True
) -> Task:
    """Gets the current valid task for all application types.

    Also ensure the application is in the correct status for the supplied task.
    """

    if case_type in ["import", "export"]:
        st = ImpExpStatus

        # importer/exporter edit the application
        # it can either be:
        #  - a fresh new application (IN_PROGRESS)
        #  - an update requested (PROCESSING/VARIATION_REQUESTED)
        if task_type == Task.TaskType.PREPARE:
            return application.get_task(
                [st.IN_PROGRESS, st.PROCESSING, st.VARIATION_REQUESTED],
                task_type,
                select_for_update,
            )

        elif task_type == Task.TaskType.PROCESS:
            return application.get_task(
                [st.SUBMITTED, st.PROCESSING, st.VARIATION_REQUESTED], task_type, select_for_update
            )

        elif task_type == Task.TaskType.AUTHORISE:
            return application.get_task(
                [application.Statuses.PROCESSING, st.VARIATION_REQUESTED],
                task_type,
                select_for_update,
            )

        elif task_type in [Task.TaskType.CHIEF_WAIT, Task.TaskType.CHIEF_ERROR]:
            return application.get_task(
                [st.PROCESSING, st.VARIATION_REQUESTED], task_type, select_for_update
            )

        elif task_type == Task.TaskType.REJECTED:
            return application.get_task(st.COMPLETED, task_type, select_for_update)

    elif case_type == "access":
        if task_type == Task.TaskType.PROCESS:
            return application.get_task(
                application.Statuses.SUBMITTED, task_type, select_for_update
            )

    raise NotImplementedError(
        f"State not supported for app: '{application.process_type}', case type: '{case_type}'"
        f" and task type: '{task_type}'."
    )


def end_process_task(task: Task, user: "User" = None) -> None:
    """End the supplied task.

    :param task: Task instance
    :param user: User who ended the task
    """

    task.is_active = False
    task.finished = timezone.now()

    if user:
        task.owner = user

    task.save()


def view_application_file(
    user: User, application: ImpOrExpOrAccess, related_file_model: Any, file_pk: int, case_type: str
) -> HttpResponse:

    check_application_permission(application, user, case_type)

    document = related_file_model.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


def view_application_file_direct(
    user: User, application: ImpOrExpOrAccess, document: File, case_type: str
) -> HttpResponse:

    check_application_permission(application, user, case_type)

    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


def get_case_page_title(case_type: str, application: ImpOrExpOrAccess, page: str) -> str:
    if case_type in ("import", "export"):
        return f"{ProcessTypes(application.process_type).label} - {page}"
    elif case_type == "access":
        return f"Access Request - {page}"
    else:
        raise NotImplementedError(f"Unknown case_type {case_type}")


# TODO: Revisit when implementing ICMSLST-1400
def create_acknowledge_notification_task(application: ImpOrExp, previous_task: Optional[Task]):
    """Create an ack task and clear the application acknowledged fields.

    This will be updated in ICMSLST-1400 to support keeping a history of multiple notifications.
    """

    Task.objects.create(process=application, task_type=Task.TaskType.ACK, previous=previous_task)

    if application.acknowledged_by or application.acknowledged_datetime:
        application.acknowledged_by = None
        application.acknowledged_datetime = None

    application.save()


def _has_importer_exporter_access(user: User, case_type: str) -> bool:
    if case_type == "import":
        return user.has_perm("web.importer_access")
    elif case_type == "export":
        return user.has_perm("web.exporter_access")

    raise NotImplementedError(f"Unknown case_type {case_type}")


# TODO: Revisit when implementing ICMSLST-1405
# Not decided where the next_sequence_value is coming from yet.
def get_import_application_licence_reference(
    licence_type: Literal["electronic", "paper"],
    process_type: str,
    next_sequence_value: int,
):
    """Creates an import application licence reference.

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
            ProcessTypes.DEROGATIONS: "SAN",
            ProcessTypes.FA_DFL: "SIL",
            ProcessTypes.FA_OIL: "OIL",
            ProcessTypes.FA_SIL: "SIL",
            ProcessTypes.IRON_STEEL: "AOG",
            ProcessTypes.SPS: "AOG",
            ProcessTypes.SANCTIONS: "SAN",
            ProcessTypes.TEXTILES: "TEX",
        }
        xxx = prefix[process_type]  # type: ignore[index]

        return f"GB{xxx}{sequence_and_check_digit}"

    return sequence_and_check_digit


def _get_check_digit(val: int) -> str:
    idx = val % 13
    return "ABCDEFGHXJKLM"[idx]


# TODO: Revisit when implementing ICMSLST-1405
# Not decided where the next_sequence_value is coming from yet.
def get_export_application_certificate_reference(process_type: str, next_sequence_value: int):
    """Creates an export application certificate reference.

    Reference formats:
        - XXX/YYYY/NNNNN

    Reference breakdown:
        - XXX: licence category
        - YYYY: year certificate issued
        - NNNNN: Next sequence value (padded to 5 digits)
    """

    today = datetime.date.today()

    prefix = {ProcessTypes.CFS: "CFS", ProcessTypes.COM: "COM", ProcessTypes.GMP: "GMP"}
    xxx = prefix[process_type]  # type: ignore[index]

    return f"{xxx}/{today.year}/{next_sequence_value:05}"
