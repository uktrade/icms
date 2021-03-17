from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.http import require_GET, require_POST
from s3chunkuploader.file_handler import s3_client

from web.domains.case._import.models import ImportApplication
from web.domains.file.views import handle_uploaded_file

from .forms import PrepareWoodQuotaForm, SupportingDocumentForm
from .models import WoodQuotaApplication


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_wood_quota(request, pk):
    with transaction.atomic():
        application = get_object_or_404(WoodQuotaApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = PrepareWoodQuotaForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(reverse("import:wood:edit-quota", kwargs={"pk": pk}))

        else:
            form = PrepareWoodQuotaForm(instance=application, initial={"contact": request.user})

        # TODO: after ICMSLST-602 is done, we'll know whether we need to filter
        # by error_message being None or not
        supporting_documents = application.supporting_documents.filter(is_active=True)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Wood (Quota) Import Licence",
            "supporting_documents": supporting_documents,
        }

        return render(request, "web/domains/case/import/wood/edit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def add_supporting_document(request, pk):
    with transaction.atomic():
        application = get_object_or_404(WoodQuotaApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = SupportingDocumentForm(data=request.POST, files=request.FILES)
            document = request.FILES.get("document")

            if form.is_valid():
                handle_uploaded_file(document, request.user, application.supporting_documents)

                return redirect(reverse("import:wood:edit-quota", kwargs={"pk": pk}))
        else:
            form = SupportingDocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Wood (Quota) Import Licence - Add supporting document",
        }

        return render(request, "web/domains/case/import/wood/add_supporting_document.html", context)


@require_GET
@login_required
def view_supporting_document(request, application_pk, document_pk):
    has_perm_importer = request.user.has_perm("web.importer_access")
    has_perm_reference_data = request.user.has_perm("web.reference_data_access")

    if not has_perm_importer and not has_perm_reference_data:
        raise PermissionDenied

    with transaction.atomic():
        application = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        # first check is for case managers (who are not marked as contacts of
        # importers), second is for people submitting applications
        if not has_perm_reference_data and not request.user.has_perm(
            "web.is_contact_of_importer", application.importer
        ):
            raise PermissionDenied

        document = application.supporting_documents.get(pk=document_pk)

        client = s3_client()

        s3_file = client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=document.path)
        s3_file_content = s3_file["Body"].read()

        response = HttpResponse(content=s3_file_content, content_type=document.content_type)
        response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

        return response


@require_POST
@login_required
@permission_required("web.importer_access", raise_exception=True)
def delete_supporting_document(request, application_pk, document_pk):
    with transaction.atomic():
        application = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:wood:edit-quota", kwargs={"pk": application_pk}))
