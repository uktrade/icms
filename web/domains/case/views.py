from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from web.domains.file.views import handle_uploaded_file

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
