from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from web.domains.file.views import handle_uploaded_file
from web.domains.template.models import Template
from web.flow.models import Task
from web.notify import notify

from . import forms, models
from .fir import forms as fir_forms
from .fir.models import FurtherInformationRequest


def _list_notes(request, application_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(
            klass=model_class.objects.select_for_update(), pk=application_pk
        )
        application.get_task(model_class.SUBMITTED, "process")
        context = {
            "process_template": f"web/domains/case/{url_namespace}/partials/process.html",
            "process": application,
            "notes": application.case_notes,
            "url_namespace": url_namespace,
        }
    return render(
        request=request,
        template_name="web/domains/case/list-notes.html",
        context=context,
    )


def _add_note(request, application_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")
        application.case_notes.create(status=models.CASE_NOTE_DRAFT, created_by=request.user)

    return redirect(reverse(f"{url_namespace}:list-notes", kwargs={"pk": application_pk}))


def _archive_note(request, application_pk, note_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")
        application.case_notes.filter(pk=note_pk).update(is_active=False)

    return redirect(reverse(f"{url_namespace}:list-notes", kwargs={"pk": application_pk}))


def _unarchive_note(request, application_pk, note_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")
        application.case_notes.filter(pk=note_pk).update(is_active=True)

    return redirect(reverse(f"{url_namespace}:list-notes", kwargs={"pk": application_pk}))


def _edit_note(request, application_pk, note_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")
        note = application.case_notes.get(pk=note_pk)
        if request.POST:
            note_form = forms.CaseNoteForm(request.POST, instance=note)
            files = request.FILES.getlist("files")
            if note_form.is_valid():
                note_form.save()
                for f in files:
                    handle_uploaded_file(f, request.user, note.files)
                return redirect(
                    reverse(
                        f"{url_namespace}:edit-note",
                        kwargs={"application_pk": application_pk, "note_pk": note_pk},
                    )
                )
        else:
            note_form = forms.CaseNoteForm(instance=note)

        context = {
            "process_template": f"web/domains/case/{url_namespace}/partials/process.html",
            "process": application,
            "note_form": note_form,
            "note": note,
            "url_namespace": url_namespace,
        }

    return render(
        request=request,
        template_name="web/domains/case/edit-note.html",
        context=context,
    )


def archive_file_note(request, application_pk, note_pk, file_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")
        document = application.case_notes.get(pk=note_pk).files.get(pk=file_pk)
        document.is_active = False
        document.save()

    return redirect(
        reverse(
            f"{url_namespace}:edit-note",
            kwargs={"application_pk": application_pk, "note_pk": note_pk},
        )
    )


def _manage_update_requests(
    request, application, model_class, email_subject, email_content, contacts, url_namespace
):
    with transaction.atomic():
        task = application.get_task([model_class.SUBMITTED, model_class.WITHDRAWN], "process")
        update_requests = application.update_requests.filter(is_active=True)
        current_update_request = update_requests.filter(
            status__in=[models.UpdateRequest.OPEN, models.UpdateRequest.UPDATE_IN_PROGRESS]
        ).first()

        if request.POST:
            form = forms.UpdateRequestForm(request.POST)
            if form.is_valid():
                update_request = form.save(commit=False)
                update_request.requested_by = request.user
                update_request.request_datetime = timezone.now()
                update_request.status = models.UpdateRequest.OPEN
                update_request.save()

                application.status = model_class.UPDATE_REQUESTED
                application.save()
                application.update_requests.add(update_request)

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                Task.objects.create(process=application, task_type="prepare", previous=task)

                notify.update_request(
                    email_subject, email_content, contacts, update_request.email_cc_address_list
                )

                return redirect(reverse("workbasket"))
        else:
            form = forms.UpdateRequestForm(
                initial={
                    "request_subject": email_subject,
                    "request_detail": email_content,
                }
            )

        context = {
            "process_template": f"web/domains/case/{url_namespace}/partials/process.html",
            "process": application,
            "task": task,
            "page_title": f"{application.application_type.get_type_description()} - Update Requests",
            "form": form,
            "update_requests": update_requests,
            "current_update_request": current_update_request,
            "url_namespace": url_namespace,
        }

        return render(
            request=request,
            template_name="web/domains/case/update-requests.html",
            context=context,
        )


def _close_update_requests(request, application_pk, update_request_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        task = application.get_task(model_class.UPDATE_REQUESTED, "process")

        application.status = model_class.SUBMITTED

        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(process=application, task_type="process", previous=task)

        update_request = application.update_requests.get(pk=update_request_pk)
        update_request.status = models.UpdateRequest.CLOSED
        update_request.closed_by = request.user
        update_request.closed_datetime = timezone.now()
        update_request.save()

    return redirect(
        reverse(
            f"{url_namespace}:manage-update-requests",
            kwargs={"application_pk": application_pk},
        )
    )


def _manage_firs(request, application_pk, model_class, url_namespace, **extra_context):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        task = application.get_task(model_class.SUBMITTED, "process")
        context = {
            "process_template": f"web/domains/case/{url_namespace}/partials/process.html",
            "process": application,
            "task": task,
            "firs": application.further_information_requests.exclude(
                status=FurtherInformationRequest.DELETED
            ),
            "url_namespace": url_namespace,
            "page_title": "Further Information Requests",
            **extra_context,
        }
    return render(
        request=request,
        template_name="web/domains/case/manage-firs.html",
        context=context,
    )


def _add_fir(request, application_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")
        template = Template.objects.get(template_code="IAR_RFI_EMAIL", is_active=True)
        # TODO: use case reference
        title_mapping = {"REQUEST_REFERENCE": application.pk}
        content_mapping = {
            "REQUESTER_NAME": application.submitted_by,
            "CURRENT_USER_NAME": request.user,
            "REQUEST_REFERENCE": application.pk,
        }
        fir = application.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=request.user,
            request_subject=template.get_title(title_mapping),
            request_detail=template.get_content(content_mapping),
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

        Task.objects.create(process=fir, task_type="check_draft", owner=request.user)

    return redirect(
        reverse(
            f"{url_namespace}:manage-firs",
            kwargs={"application_pk": application_pk},
        )
    )


def _edit_fir(request, application_pk, fir_pk, model_class, url_namespace, contacts):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        fir = get_object_or_404(application.further_information_requests.draft(), pk=fir_pk)

        task = application.get_task(model_class.SUBMITTED, "process")
        fir_task = fir.get_task(FurtherInformationRequest.DRAFT, "check_draft")

        if request.POST:
            form = fir_forms.FurtherInformationRequestForm(request.POST, instance=fir)
            files = request.FILES.getlist("files")
            if form.is_valid():
                fir = form.save()
                for f in files:
                    handle_uploaded_file(f, request.user, fir.files)

                if "send" in form.data:
                    fir.status = FurtherInformationRequest.OPEN
                    fir.save()
                    notify.further_information_requested(fir, contacts)

                    fir_task.is_active = False
                    fir_task.finished = timezone.now()
                    fir_task.save()

                    Task.objects.create(process=fir, task_type="notify_contacts", previous=fir_task)

                return redirect(
                    reverse(
                        f"{url_namespace}:manage-firs",
                        kwargs={"application_pk": application_pk},
                    )
                )
        else:
            form = fir_forms.FurtherInformationRequestForm(instance=fir)

        context = {
            "process_template": f"web/domains/case/{url_namespace}/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "fir": fir,
            "url_namespace": url_namespace,
        }

    return render(
        request=request,
        template_name="web/domains/case/edit-fir.html",
        context=context,
    )


def _archive_fir(request, application_pk, fir_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        application.get_task(model_class.SUBMITTED, "process")
        fir_tasks = fir.get_active_tasks()

        fir.is_active = False
        fir.status = FurtherInformationRequest.DELETED
        fir.save()

        fir_tasks.update(is_active=False, finished=timezone.now())

    return redirect(
        reverse(
            f"{url_namespace}:manage-firs",
            kwargs={"application_pk": application_pk},
        )
    )


def _withdraw_fir(request, application_pk, fir_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        application.get_task(model_class.SUBMITTED, "process")
        fir_task = fir.get_task(FurtherInformationRequest.OPEN, "notify_contacts")

        fir.status = FurtherInformationRequest.DRAFT
        fir.save()

        fir_task.is_active = False
        fir_task.finished = timezone.now()
        fir_task.save()

        Task.objects.create(process=fir, task_type="check_draft", previous=fir_task)

        application.further_information_requests.filter(pk=fir_pk).update(
            is_active=True, status=FurtherInformationRequest.DRAFT
        )

    return redirect(
        reverse(
            f"{url_namespace}:manage-firs",
            kwargs={"application_pk": application_pk},
        )
    )


def _close_fir(request, application_pk, fir_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)
        fir_task = fir.get_task(
            [FurtherInformationRequest.OPEN, FurtherInformationRequest.RESPONDED], "responded"
        )

        fir.status = FurtherInformationRequest.CLOSED
        fir.save()

        fir_task.is_active = False
        fir_task.finished = timezone.now()
        fir_task.save()

        application.further_information_requests.filter(pk=fir_pk).update(
            is_active=False, status=FurtherInformationRequest.CLOSED
        )

    return redirect(
        reverse(
            f"{url_namespace}:manage-firs",
            kwargs={"application_pk": application_pk},
        )
    )


def _archive_fir_file(request, application_pk, fir_pk, file_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")
        document = application.further_information_requests.get(pk=fir_pk).files.get(pk=file_pk)
        document.is_active = False
        document.save()

    return redirect(
        reverse(
            f"{url_namespace}:edit-fir",
            kwargs={"application_pk": application_pk, "fir_pk": fir_pk},
        )
    )


def _list_firs(request, application_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        application.get_task(model_class.SUBMITTED, "process")

    context = {
        "process": application,
        "process_template": f"web/domains/case/{url_namespace}/partials/process.html",
        "firs": application.further_information_requests.filter(
            Q(status=FurtherInformationRequest.OPEN)
            | Q(status=FurtherInformationRequest.RESPONDED)
            | Q(status=FurtherInformationRequest.CLOSED)
        ),
        "url_namespace": url_namespace,
    }
    return render(request, "web/domains/case/list-firs.html", context)


def _respond_fir(request, application_pk, fir_pk, model_class, url_namespace):
    with transaction.atomic():
        application = get_object_or_404(model_class.objects.select_for_update(), pk=application_pk)
        fir = get_object_or_404(application.further_information_requests.open(), pk=fir_pk)

        application.get_task(model_class.SUBMITTED, "process")
        fir_task = fir.get_task(FurtherInformationRequest.OPEN, "notify_contacts")

        if request.POST:
            form = fir_forms.FurtherInformationRequestResponseForm(instance=fir, data=request.POST)
            files = request.FILES.getlist("files")
            if form.is_valid():
                fir = form.save()
                for f in files:
                    handle_uploaded_file(f, request.user, fir.files)

                fir.response_datetime = timezone.now()
                fir.status = FurtherInformationRequest.RESPONDED
                fir.response_by = request.user
                fir.save()

                fir_task.is_active = False
                fir_task.finished = timezone.now()
                fir_task.save()

                Task.objects.create(process=fir, task_type="responded", owner=request.user)

                notify.further_information_responded(application, fir)

                return redirect(reverse("workbasket"))
        else:
            form = fir_forms.FurtherInformationRequestResponseForm(instance=fir)

    context = {
        "process": application,
        "process_template": f"web/domains/case/{url_namespace}/partials/process.html",
        "fir": fir,
        "form": form,
        "url_namespace": url_namespace,
    }
    return render(request, "web/domains/case/respond-fir.html", context)
