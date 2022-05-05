from typing import Any, Optional, Type

from django import forms
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.utils import timezone

from web.domains.case._import.models import ImportApplication
from web.domains.case.export.models import ExportApplication
from web.domains.case.models import CaseLicenceCertificateBase
from web.domains.file.models import File
from web.domains.user.models import User
from web.flow.models import ProcessTypes, Task
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3

from .shared import ImpExpStatus
from .types import ImpOrExp, ImpOrExpOrAccess


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


def _has_importer_exporter_access(user: User, case_type: str) -> bool:
    if case_type == "import":
        return user.has_perm("web.importer_access")
    elif case_type == "export":
        return user.has_perm("web.exporter_access")

    raise NotImplementedError(f"Unknown case_type {case_type}")


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


def set_application_licence_or_certificate_active(application: ImpOrExp) -> None:
    """Sets the latest draft licence to active and mark the previous active licence to archive."""

    if application.is_import_application():
        active_l_or_c = application.licences.filter(
            status=CaseLicenceCertificateBase.Status.ACTIVE
        ).first()
        l_or_c = application.get_most_recent_licence()
        l_or_c.case_completion_date = timezone.now().date()

    else:
        active_l_or_c = application.certificates.filter(
            status=CaseLicenceCertificateBase.Status.ACTIVE
        ).first()
        l_or_c = application.get_most_recent_certificate()
        l_or_c.issue_date = timezone.now().date()

    if active_l_or_c:
        active_l_or_c.status = CaseLicenceCertificateBase.Status.ARCHIVED
        active_l_or_c.save()

    l_or_c.status = CaseLicenceCertificateBase.Status.ACTIVE

    # Record the case_reference to see when viewing the application history
    l_or_c.case_reference = application.reference

    l_or_c.save()


def archive_application_licence_or_certificate(application: ImpOrExp) -> None:
    """Archives the draft licence or certificate."""

    if application.is_import_application():
        l_or_c = application.get_most_recent_licence()
    else:
        l_or_c = application.get_most_recent_certificate()

    l_or_c.status = l_or_c.Status.ARCHIVED
    l_or_c.save()


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


def get_application_form(
    application: ImpOrExp,
    request: AuthenticatedHttpRequest,
    edit_form: Type[forms.ModelForm],
    submit_form: Type[forms.ModelForm],
) -> forms.ModelForm:
    """Create a form instance - Used in all edit application views."""

    if request.method == "POST":
        form = edit_form(data=request.POST, instance=application)
    else:
        initial = {} if application.contact else {"contact": request.user}
        form_kwargs = {"instance": application, "initial": initial}

        # query param to fully validate the form.
        if "validate" in request.GET:
            form_kwargs["data"] = model_to_dict(application)
            form = submit_form(**form_kwargs)
        else:
            form = edit_form(**form_kwargs)

    return form
