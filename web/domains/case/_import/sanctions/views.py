from typing import Type

import structlog as logging
from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.views import check_application_permission
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .. import views as import_views
from .forms import GoodsForm, GoodsSanctionsLicenceForm, SanctionsAndAdhocLicenseForm
from .models import SanctionsAndAdhocApplication, SanctionsAndAdhocApplicationGoods

logger = logging.getLogger(__name__)


@login_required
def edit_application(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.method == "POST":
            form = SanctionsAndAdhocLicenseForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:sanctions:edit", kwargs={"application_pk": application_pk})
                )
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
def add_goods(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.method == "POST":
            goods_form = GoodsForm(request.POST)

            if goods_form.is_valid():
                obj = goods_form.save(commit=False)
                obj.import_application = application
                obj.save()

                return redirect(
                    reverse("import:sanctions:edit", kwargs={"application_pk": application_pk})
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
def edit_goods(
    request: AuthenticatedHttpRequest, *, application_pk: int, goods_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        form_class = GoodsForm
        success_url = reverse("import:sanctions:edit", kwargs={"application_pk": application_pk})
        template_name = "web/domains/case/import/sanctions/add_or_edit_goods.html"

        return _edit_goods(
            request,
            application=application,
            task=task,
            form_class=form_class,
            goods_pk=goods_pk,
            success_url=success_url,
            template_name=template_name,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_goods_licence(
    request: AuthenticatedHttpRequest, *, application_pk: int, goods_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        form_class = GoodsSanctionsLicenceForm
        success_url = reverse(
            "case:prepare-response",
            kwargs={"application_pk": application.pk, "case_type": "import"},
        )
        template_name = "web/domains/case/import/manage/response-prep-edit-form.html"

        return _edit_goods(
            request,
            application=application,
            task=task,
            form_class=form_class,
            goods_pk=goods_pk,
            success_url=success_url,
            template_name=template_name,
        )


def _edit_goods(
    request: AuthenticatedHttpRequest,
    *,
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
        "case_type": "import",
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
@require_POST
def delete_goods(
    request: AuthenticatedHttpRequest, *, application_pk: int, goods_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        get_object_or_404(application.sanctionsandadhocapplicationgoods_set, pk=goods_pk).delete()

    return redirect(reverse("import:sanctions:edit", kwargs={"application_pk": application_pk}))


@login_required
def add_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.method == "POST":
            form = DocumentForm(request.POST, request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:sanctions:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Sanctions and Adhoc License Application",
        }
        return render(request, "web/domains/case/import/sanctions/add_document.html", context)


@require_GET
@login_required
def view_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(SanctionsAndAdhocApplication, pk=application_pk)
    return import_views.view_file(
        request, application, application.supporting_documents, document_pk
    )


@require_POST
@login_required
def delete_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:sanctions:edit", kwargs={"application_pk": application_pk}))


@login_required
def submit_sanctions(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        errors = ApplicationErrors()

        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:sanctions:edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(
            SanctionsAndAdhocLicenseForm(data=model_to_dict(application), instance=application),
            page_errors,
        )
        errors.add(page_errors)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                return application.redirect_after_submit(request)

        else:
            form = SubmitForm()

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
