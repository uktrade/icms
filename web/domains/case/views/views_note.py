from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case import forms
from web.domains.case.services import case_progress
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import get_case_page_title
from web.domains.file.utils import create_file_model
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3

from .utils import get_caseworker_view_readonly_status, get_class_imp_or_exp


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def list_notes(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)

        context = {
            "process": application,
            "notes": application.case_notes,
            "has_any_case_notes": application.case_notes.exists(),
            "case_type": case_type,
            "page_title": get_case_page_title(case_type, application, "Notes"),
            "readonly_view": readonly_view,
        }

    return render(
        request=request,
        template_name="web/domains/case/manage/list-notes.html",
        context=context,
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def add_note(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        note = application.case_notes.create(created_by=request.user)

    return redirect(
        reverse(
            "case:edit-note",
            kwargs={"application_pk": application_pk, "note_pk": note.pk, "case_type": case_type},
        )
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def archive_note(
    request: AuthenticatedHttpRequest, *, application_pk: int, note_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        application.case_notes.filter(pk=note_pk).update(is_active=False, updated_by=request.user)

    return redirect(
        reverse(
            "case:list-notes", kwargs={"application_pk": application_pk, "case_type": case_type}
        )
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def unarchive_note(
    request: AuthenticatedHttpRequest, *, application_pk: int, note_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        application.case_notes.filter(pk=note_pk).update(is_active=True, updated_by=request.user)

    return redirect(
        reverse(
            "case:list-notes", kwargs={"application_pk": application_pk, "case_type": case_type}
        )
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_note(
    request: AuthenticatedHttpRequest, *, application_pk: int, note_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        note = application.case_notes.get(pk=note_pk)

        if not note.is_active:
            messages.error(request, "Editing of deleted notes is not allowed.")

            return redirect(
                reverse(
                    "case:list-notes",
                    kwargs={"application_pk": application_pk, "case_type": case_type},
                )
            )

        if request.method == "POST":
            note_form = forms.CaseNoteForm(request.POST, instance=note)

            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.updated_by = request.user
                note.save()

                return redirect(
                    reverse(
                        "case:edit-note",
                        kwargs={
                            "application_pk": application_pk,
                            "note_pk": note_pk,
                            "case_type": case_type,
                        },
                    )
                )
        else:
            note_form = forms.CaseNoteForm(instance=note)

        context = {
            "process": application,
            "note_form": note_form,
            "note": note,
            "case_type": case_type,
            "page_title": get_case_page_title(case_type, application, "Edit Note"),
        }

    return render(
        request=request,
        template_name="web/domains/case/manage/edit-note.html",
        context=context,
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def add_note_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, note_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        note = application.case_notes.get(pk=note_pk)

        if request.method == "POST":
            form = forms.DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, note.files)

                return redirect(
                    reverse(
                        "case:edit-note",
                        kwargs={
                            "application_pk": application_pk,
                            "note_pk": note_pk,
                            "case_type": case_type,
                        },
                    )
                )
        else:
            form = forms.DocumentForm()

        context = {
            "process": application,
            "form": form,
            "note": note,
            "case_type": case_type,
            "page_title": get_case_page_title(case_type, application, "Add Note"),
        }

    return render(
        request=request,
        template_name="web/domains/case/manage/add-note-document.html",
        context=context,
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_GET
def view_note_document(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    note_pk: int,
    file_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    application: ImpOrExp = get_object_or_404(model_class, pk=application_pk)
    note = application.case_notes.get(pk=note_pk)
    document = note.files.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def delete_note_document(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    note_pk: int,
    file_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        document = application.case_notes.get(pk=note_pk).files.get(pk=file_pk)
        document.is_active = False
        document.save()

    return redirect(
        reverse(
            "case:edit-note",
            kwargs={"application_pk": application_pk, "note_pk": note_pk, "case_type": case_type},
        )
    )
