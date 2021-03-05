from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from web.domains.file.views import handle_uploaded_file
from web.flow.models import Task
from web.notify import notify

from . import forms, models


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
