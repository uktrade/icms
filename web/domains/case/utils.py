from typing import Any, Optional

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from web.domains.case.services import case_progress, document_pack, reference
from web.flow.models import ProcessTypes
from web.mail.constants import EmailTypes
from web.mail.emails import send_application_refused_email, send_variation_request_email
from web.models import ExportApplication, ImportApplication, Task, User
from web.permissions import AppChecker
from web.types import AuthenticatedHttpRequest
from web.utils.lock_manager import LockManager
from web.utils.s3 import get_file_from_s3

from .models import VariationRequest
from .types import ImpOrExp, ImpOrExpOrAccess


def end_process_task(task: Task, user: Optional["User"] = None) -> None:
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
    user: User, application: ImpOrExp, related_file_model: Any, file_pk: int
) -> HttpResponse:
    checker = AppChecker(user, application)

    if not checker.can_view():
        raise PermissionDenied

    document = related_file_model.get(pk=file_pk)
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


def get_application_form(
    application: ImpOrExp,
    request: AuthenticatedHttpRequest,
    edit_form: type[forms.ModelForm],
    submit_form: type[forms.ModelForm],
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


def submit_application(app: ImpOrExp, request: AuthenticatedHttpRequest, task: Task) -> None:
    """Helper function to submit all types of application."""

    if not app.reference:
        app.reference = reference.get_application_case_reference(
            request.icms.lock_manager, application=app
        )

    # if case owner is present, an update request has just been filed
    if app.case_owner:
        # Only change to processing if it's not a variation request
        if app.status != app.Statuses.VARIATION_REQUESTED:
            app.status = app.Statuses.PROCESSING
    else:
        app.status = app.Statuses.SUBMITTED

    current_date_time = timezone.now()
    if not app.submit_datetime:
        app.submit_datetime = current_date_time
    app.last_submit_datetime = current_date_time
    app.submitted_by = request.user
    app.update_order_datetime()
    app.save()

    task.is_active = False
    task.finished = timezone.now()
    task.save()

    # Only create a PROCESS Task if one doesn't exist.
    # One will already exist if the applicant is submitting an application after an
    # update request from ILB.
    Task.objects.get_or_create(
        process=app, task_type=Task.TaskType.PROCESS, is_active=True, defaults={"previous": task}
    )


def redirect_after_submit(app: ImpOrExp, request: AuthenticatedHttpRequest) -> HttpResponse:
    """Called after submitting an application"""

    msg = (
        "Your application has been submitted."
        f" The reference number assigned to this case is {app.get_reference()}."
    )
    messages.success(request, msg)

    return redirect(reverse("workbasket"))


def application_history(app_reference: str, is_import: bool = True) -> None:
    """Debug method to print the history of the application

    >>> import importlib as im; from web.domains.case import utils
    >>> im.reload(utils); utils.application_history("IMA/2023/00001")
    """

    if is_import:
        app = ImportApplication.objects.get(reference__startswith=app_reference)
    else:
        app = ExportApplication.objects.get(reference__startswith=app_reference)

    app = app.get_specific_model()

    print("*-" * 40)
    print(f"Current status: {app.get_status_display()}")

    all_tasks = app.tasks.all().order_by("created")
    active = all_tasks.filter(is_active=True)

    print("\nActive Tasks in order:")
    for t in active:
        print(f"Task: {t.get_task_type_display()}, created={t.created}, finished={t.finished}")

    print("\nAll tasks in order:")
    for t in all_tasks:
        print(f"Task: {t.get_task_type_display()}, created={t.created}, finished={t.finished}")

    print("*-" * 40)

    for p in document_pack._get_qm(app).order_by("created_at"):
        print(f"DocumentPack: {p}")


def start_application_authorisation(application: ImpOrExp, lock_manager: LockManager) -> None:
    """Start the authorisation process for the application.

    :param app: The application to authorise
    :param user: The user starting the authorisation process
    """

    task = case_progress.get_expected_task(application, Task.TaskType.PROCESS)

    create_documents = True
    send_vr_email = False

    if application.status == application.Statuses.VARIATION_REQUESTED:
        if (
            application.is_import_application()
            and application.variation_decision == application.REFUSE
        ):
            vr = application.variation_requests.get(status=VariationRequest.Statuses.OPEN)
            next_task = None
            application.status = application.Statuses.COMPLETED
            vr.status = VariationRequest.Statuses.REJECTED
            vr.reject_cancellation_reason = application.variation_refuse_reason
            vr.closed_datetime = timezone.now()
            vr.save()
            send_vr_email = True
            create_documents = False
        else:
            next_task = Task.TaskType.AUTHORISE

    else:
        if application.decision == application.REFUSE:
            next_task = Task.TaskType.REJECTED
            application.status = application.Statuses.COMPLETED
            create_documents = False

        else:
            next_task = Task.TaskType.AUTHORISE
            application.status = application.Statuses.PROCESSING

    application.update_order_datetime()
    application.save()

    end_process_task(task)

    if next_task:
        Task.objects.create(process=application, task_type=next_task, previous=task)

    if create_documents:
        document_pack.doc_ref_documents_create(application, lock_manager)
    else:
        document_pack.pack_draft_archive(application)

    if (
        application.decision == application.REFUSE
        and application.status == application.Statuses.COMPLETED
    ):
        send_application_refused_email(application)

    if send_vr_email:
        send_variation_request_email(
            vr, EmailTypes.APPLICATION_VARIATION_REQUEST_REFUSED, application
        )


def authorise_application_documents(application: ImpOrExp, user) -> None:
    """Authorise the documents for the application.

    :param application: The application to authorise
    :param user: The user authorising the documents
    """
    from .tasks import create_case_document_pack

    task = case_progress.get_expected_task(application, Task.TaskType.AUTHORISE)
    end_process_task(task, user)
    Task.objects.create(
        process=application, task_type=Task.TaskType.DOCUMENT_SIGNING, previous=task
    )

    application.update_order_datetime()
    application.save()

    # Queues all documents to be created
    create_case_document_pack(application, user)
