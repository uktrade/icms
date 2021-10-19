from typing import Any, Optional

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone

from web.domains.case._import.models import ImportApplication
from web.domains.case.export.models import ExportApplication
from web.domains.file.models import File
from web.domains.user.models import User
from web.flow.models import ProcessTypes, Task
from web.models.models import CaseReference
from web.utils.lock_manager import LockManager
from web.utils.s3 import get_file_from_s3

from .types import ImpOrExpOrAccess


# TODO: ICMSLST-1175 Rename CaseReference
def allocate_case_reference(
    *, lock_manager: LockManager, prefix: str, use_year: bool, min_digits: int
) -> str:
    """Allocate and return new case reference.

    NOTE: If case reference logic grows beyond this, consider a proper service
    layer."""

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

    new_ref_str = "%0*d" % (min_digits, new_ref)

    if use_year:
        return "/".join([prefix, str(year), new_ref_str])
    else:
        return "/".join([prefix, new_ref_str])


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
    application: ImpOrExpOrAccess, case_type: str, task_type: str
) -> Task:
    """Gets the current valid task for all application types.

    Also ensure the application is in the correct status for the supplied task.
    """

    if case_type in ["import", "export"]:
        st = ImportApplication.Statuses

        # importer/exporter edit the application
        # it can either be:
        #  - a fresh new application (IN_PROGRESS)
        #  - an update requested (PROCESSING)
        if task_type == Task.TaskType.PREPARE:
            return application.get_task([st.IN_PROGRESS, st.PROCESSING], task_type)

        elif task_type == Task.TaskType.PROCESS:
            return application.get_task([st.SUBMITTED, st.PROCESSING], task_type)

        elif task_type == Task.TaskType.AUTHORISE:
            return application.get_task(application.Statuses.PROCESSING, task_type)

        elif task_type in [Task.TaskType.CHIEF_WAIT, Task.TaskType.CHIEF_ERROR]:
            return application.get_task(application.Statuses.PROCESSING, task_type)

        elif task_type in Task.TaskType.ACK:
            return application.get_task(application.Statuses.COMPLETED, task_type)

    elif case_type == "access":
        if task_type == Task.TaskType.PROCESS:
            return application.get_task(application.Statuses.SUBMITTED, task_type)

    raise NotImplementedError(
        f"State not supported for app: '{application.process_type}', case type: '{case_type}'"
        f" and task type: '{task_type}'."
    )


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


def _has_importer_exporter_access(user: User, case_type: str) -> bool:
    if case_type == "import":
        return user.has_perm("web.importer_access")
    elif case_type == "export":
        return user.has_perm("web.exporter_access")

    raise NotImplementedError(f"Unknown case_type {case_type}")
