import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.file.views import handle_uploaded_file
from web.domains.template.models import Template
from web.flow.models import Task

from .. import views as import_views
from .forms import (
    GoodsForm,
    SanctionsAndAdhocLicenseForm,
    SubmitSanctionsForm,
    SupportingDocumentForm,
)
from .models import SanctionsAndAdhocApplication, SanctionsAndAdhocApplicationGoods

logger = logging.getLogger(__name__)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_sanctions_and_adhoc_licence_application(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        application_started = False
        if application.origin_country is not None and application.consignment_country is not None:
            application_started = True

        if request.method == "POST":
            form = SanctionsAndAdhocLicenseForm(data=request.POST, instance=application)
            if form.is_valid():
                form.save()
                return redirect(
                    reverse(
                        "import:sanctions:edit-sanctions-and-adhoc-licence-application",
                        kwargs={"pk": pk},
                    )
                )
        else:
            form = SanctionsAndAdhocLicenseForm(
                instance=application, initial={"contact": request.user}
            )

        supporting_documents = application.supporting_documents.filter(is_active=True)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "application_started": application_started,
            "page_title": "Sanctions and Adhoc License Application",
            "goods_list": SanctionsAndAdhocApplicationGoods.objects.filter(
                import_application=application
            ),
            "supporting_documents": supporting_documents,
        }
        return render(
            request,
            "web/domains/case/import/sanctions/edit_sanctions_and_adhoc_licence_application.html",
            context,
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def add_goods(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.method == "POST":
            goods_form = GoodsForm(request.POST)
            if goods_form.is_valid():
                obj = goods_form.save(commit=False)
                obj.import_application = application
                obj.save()
                return redirect(
                    reverse(
                        "import:sanctions:edit-sanctions-and-adhoc-licence-application",
                        kwargs={"pk": pk},
                    )
                )
        else:
            goods_form = GoodsForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": goods_form,
            "page_title": "Sanctions and Adhoc License Application",
        }
        return render(
            request,
            "web/domains/case/import/sanctions/add_or_edit_goods.html",
            context,
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_goods(request, application_pk, goods_pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        goods = get_object_or_404(application.sanctionsandadhocapplicationgoods_set, pk=goods_pk)

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.method == "POST":
            form = GoodsForm(request.POST, instance=goods)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.import_application = application
                obj.save()
                return redirect(
                    reverse(
                        "import:sanctions:edit-sanctions-and-adhoc-licence-application",
                        kwargs={"pk": application_pk},
                    )
                )
        else:
            form = GoodsForm(instance=goods)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Sanctions and Adhoc License Application",
        }
        return render(
            request,
            "web/domains/case/import/sanctions/add_or_edit_goods.html",
            context,
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def delete_goods(request, application_pk, goods_pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )
        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        get_object_or_404(application.sanctionsandadhocapplicationgoods_set, pk=goods_pk).delete()

    return redirect(
        reverse(
            "import:sanctions:edit-sanctions-and-adhoc-licence-application",
            kwargs={"pk": application_pk},
        )
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def add_supporting_document(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied
        if request.method == "POST":
            documents_form = SupportingDocumentForm(request.POST, request.FILES)
            document = request.FILES.get("document")
            if documents_form.is_valid():
                handle_uploaded_file(document, request.user, application.supporting_documents)
                return redirect(
                    reverse(
                        "import:sanctions:edit-sanctions-and-adhoc-licence-application",
                        kwargs={"pk": pk},
                    )
                )
        else:
            documents_form = SupportingDocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": documents_form,
            "page_title": "Sanctions and Adhoc License Application",
        }
        return render(
            request,
            "web/domains/case/import/sanctions/add_document.html",
            context,
        )


@require_GET
@login_required
def view_supporting_document(request, application_pk, document_pk):
    application = get_object_or_404(SanctionsAndAdhocApplication, pk=application_pk)
    return import_views._view_file(
        request, application, application.supporting_documents, document_pk
    )


@require_POST
@login_required
@permission_required("web.importer_access", raise_exception=True)
def delete_supporting_document(request, application_pk, document_pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse(
                "import:sanctions:edit-sanctions-and-adhoc-licence-application",
                kwargs={"pk": application_pk},
            )
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def sanctions_validation_summary(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "task": task,
        "application_title": "Sanctions and Adhoc License Application",
    }
    return render(
        request, "web/domains/case/import/sanctions/sanctions_validation_summary.html", context
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def submit_sanctions(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = SubmitSanctionsForm(data=request.POST)

            if form.is_valid():
                application.status = ImportApplication.SUBMITTED
                application.submit_datetime = timezone.now()
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                Task.objects.create(process=application, task_type="process", previous=task)

                return redirect(reverse("home"))

        else:
            form = SubmitSanctionsForm()

    declaration = Template.objects.filter(
        is_active=True,
        template_type=Template.DECLARATION,
        application_domain=Template.IMPORT_APPLICATION,
        template_code="IMA_GEN_DECLARATION",
    ).first()

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "task": task,
        "form": form,
        "application_title": "Sanctions and Adhoc License Application",
        "declaration": declaration,
    }
    return render(request, "web/domains/case/import/sanctions/submit.html", context)
