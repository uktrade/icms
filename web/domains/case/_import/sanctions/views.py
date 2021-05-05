from typing import Type

import structlog as logging
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.notify import email
from web.utils.s3 import get_file_from_s3, get_s3_client
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .. import views as import_views
from .forms import (
    GoodsForm,
    GoodsSanctionsLicenceForm,
    SanctionEmailMessageForm,
    SanctionEmailMessageResponseForm,
    SanctionsAndAdhocLicenseForm,
    SubmitSanctionsForm,
    SupportingDocumentForm,
)
from .models import (
    SanctionEmailMessage,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
)

logger = logging.getLogger(__name__)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_application(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.method == "POST":
            form = SanctionsAndAdhocLicenseForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(reverse("import:sanctions:edit-application", kwargs={"pk": pk}))
        else:
            form = SanctionsAndAdhocLicenseForm(
                instance=application, initial={"contact": request.user}
            )

        supporting_documents = application.supporting_documents.filter(is_active=True)
        goods_list = SanctionsAndAdhocApplicationGoods.objects.filter(
            import_application=application
        )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Sanctions and Adhoc License Application - Edit",
            "goods_list": goods_list,
            "supporting_documents": supporting_documents,
        }
        return render(request, "web/domains/case/import/sanctions/edit_application.html", context)


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
                return redirect(reverse("import:sanctions:edit-application", kwargs={"pk": pk}))
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
def edit_goods(request: HttpRequest, application_pk: int, goods_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        form_class = GoodsForm
        success_url = reverse("import:sanctions:edit-application", kwargs={"pk": application_pk})
        template_name = "web/domains/case/import/sanctions/add_or_edit_goods.html"

        return _edit_goods(
            request, application, task, form_class, goods_pk, success_url, template_name
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_goods_licence(request: HttpRequest, application_pk: int, goods_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        form_class = GoodsSanctionsLicenceForm
        success_url = reverse("import:prepare-response", kwargs={"pk": application.pk})
        template_name = "web/domains/case/import/manage/edit-goods-licence.html"

        return _edit_goods(
            request, application, task, form_class, goods_pk, success_url, template_name
        )


def _edit_goods(
    request: HttpRequest,
    application: SanctionsAndAdhocApplication,
    task: Task,
    form_class: Type[forms.ModelForm],
    goods_pk: int,
    success_url: str,
    template_name: str,
) -> HttpResponse:
    goods = get_object_or_404(application.sanctionsandadhocapplicationgoods_set, pk=goods_pk)

    if request.POST:
        form = form_class(request.POST, instance=goods)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.import_application = application
            obj.save()
            return redirect(success_url)
    else:
        form = form_class(instance=goods)

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "task": task,
        "form": form,
        "page_title": "Edit Goods",
    }
    return render(
        request,
        template_name,
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

    return redirect(reverse("import:sanctions:edit-application", kwargs={"pk": application_pk}))


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
                create_file_model(document, request.user, application.supporting_documents)
                return redirect(reverse("import:sanctions:edit-application", kwargs={"pk": pk}))
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
    return import_views.view_file(
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

        return redirect(reverse("import:sanctions:edit-application", kwargs={"pk": application_pk}))


@login_required
@permission_required("web.importer_access", raise_exception=True)
def submit_sanctions(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        errors = ApplicationErrors()

        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:sanctions:edit-application", kwargs={"pk": pk}),
        )
        create_page_errors(
            SanctionsAndAdhocLicenseForm(data=model_to_dict(application), instance=application),
            page_errors,
        )
        errors.add(page_errors)

        if request.POST:
            form = SubmitSanctionsForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
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
        "errors": errors if errors.has_errors() else None,
    }
    return render(request, "web/domains/case/import/sanctions/submit.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_sanction_emails(request: HttpRequest, pk: int) -> HttpResponse:
    application = get_object_or_404(SanctionsAndAdhocApplication, pk=pk)

    with transaction.atomic():
        task = application.get_task(ImportApplication.SUBMITTED, "process")

    context = {
        "process": application,
        "task": task,
        "page_title": "Sanction Emails",
        "sanction_email_messages": application.sanction_emails.filter(is_active=True),
    }

    return render(
        request=request,
        template_name="web/domains/case/import/sanctions/manage/sanction-emails.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def create_sanction_email(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        application.get_task(ImportApplication.SUBMITTED, "process")

        # TODO: template missing from db export
        # search IMA_SANCTION_EMAIL to see data migration
        template = Template.objects.get(is_active=True, template_code="IMA_SANCTION_EMAIL")
        goods_descriptions = application.sanctionsandadhocapplicationgoods_set.values_list(
            "goods_description", flat=True
        )
        body = template.get_content(
            {
                # TODO: replace with case reference
                "CASE_REFERENCE": application.pk,
                "IMPORTER_NAME": application.importer.display_name,
                "IMPORTER_ADDRESS": application.importer_office,
                "GOODS_DESCRIPTION": "\n".join(goods_descriptions),
                "CASE_OFFICER_NAME": request.user.full_name,
                "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
                "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
            }
        )
        sanction_email = SanctionEmailMessage.objects.create(
            application=application,
            status=SanctionEmailMessage.DRAFT,
            subject=template.template_title,
            body=body,
        )

        return redirect(
            reverse(
                "import:sanctions:edit-sanction-email",
                kwargs={
                    "application_pk": application.pk,
                    "sanction_email_pk": sanction_email.pk,
                },
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_sanction_email(
    request: HttpRequest, application_pk: int, sanction_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.SUBMITTED, "process")
        sanction_email = get_object_or_404(
            application.sanction_emails.filter(is_active=True), pk=sanction_email_pk
        )

        if request.POST:
            form = SanctionEmailMessageForm(request.POST, instance=sanction_email)
            if form.is_valid():
                sanction_email = form.save()

                if "send" in request.POST:
                    attachments = []
                    s3_client = get_s3_client()

                    for document in sanction_email.attachments.all():
                        file_content = get_file_from_s3(document.path, client=s3_client)
                        attachments.append((document.filename, file_content))

                    email.send_email(
                        sanction_email.subject,
                        sanction_email.body,
                        [sanction_email.to],
                        sanction_email.cc_address_list.split(","),
                        attachments,
                    )

                    sanction_email.status = SanctionEmailMessage.OPEN
                    sanction_email.sent_datetime = timezone.now()
                    sanction_email.save()

                    return redirect(
                        reverse(
                            "import:sanctions:manage-sanction-emails",
                            kwargs={"pk": application_pk},
                        )
                    )

                return redirect(
                    reverse(
                        "import:sanctions:edit-sanction-email",
                        kwargs={
                            "application_pk": application_pk,
                            "sanction_email_pk": sanction_email_pk,
                        },
                    )
                )
        else:
            form = SanctionEmailMessageForm(instance=sanction_email)

        context = {
            "process": application,
            "task": task,
            "page_title": "Edit Sanction Email",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/sanctions/manage/edit-sanction-email.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def delete_sanction_email(
    request: HttpRequest, application_pk: int, sanction_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )
        application.get_task(ImportApplication.SUBMITTED, "process")
        sanction_email = get_object_or_404(
            application.sanction_emails.filter(is_active=True), pk=sanction_email_pk
        )

        sanction_email.is_active = False
        sanction_email.save()

        return redirect(
            reverse(
                "import:sanctions:manage-sanction-emails",
                kwargs={"pk": application_pk},
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_response_sanction_email(
    request: HttpRequest, application_pk: int, sanction_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.SUBMITTED, "process")
        sanction_email = get_object_or_404(application.sanction_emails, pk=sanction_email_pk)

        if request.POST:
            form = SanctionEmailMessageResponseForm(request.POST, instance=sanction_email)
            if form.is_valid():
                sanction_email = form.save(commit=False)
                sanction_email.status = SanctionEmailMessage.CLOSED
                sanction_email.closed_datetime = timezone.now()
                sanction_email.save()

                return redirect(
                    reverse(
                        "import:sanctions:manage-sanction-emails",
                        kwargs={"pk": application_pk},
                    )
                )
        else:
            form = SanctionEmailMessageResponseForm(instance=sanction_email)

        context = {
            "process": application,
            "task": task,
            "page_title": "Add Response for Sanction Email",
            "form": form,
            "object": sanction_email,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/sanctions/manage/add-response-sanction-email.html",
            context=context,
        )
