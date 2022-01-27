import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplicationType
from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.utils import (
    check_application_permission,
    get_application_current_task,
)
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.commodity import (
    annotate_commodity_unit,
    get_commodity_group_data,
    get_commodity_unit,
    get_usage_commodities,
    get_usage_records,
)
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

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

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        if request.method == "POST":
            form = SanctionsAndAdhocLicenseForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:sanctions:edit", kwargs={"application_pk": application_pk})
                )
        else:
            initial = {} if application.contact else {"contact": request.user}
            form = SanctionsAndAdhocLicenseForm(instance=application, initial=initial)

        # Check if the main application is valid when showing add goods link
        show_add_goods = SanctionsAndAdhocLicenseForm(
            instance=application, data=model_to_dict(application)
        ).is_valid()

        supporting_documents = application.supporting_documents.filter(is_active=True)
        goods_list = SanctionsAndAdhocApplicationGoods.objects.filter(
            import_application=application
        )

        goods_list = annotate_commodity_unit(goods_list, "commodity__").distinct()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Sanctions and Adhoc License Application - Edit",
            "goods_list": goods_list,
            "supporting_documents": supporting_documents,
            "show_add_goods": show_add_goods,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/sanctions/edit_application.html", context)


@login_required
def add_goods(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        if request.method == "POST":
            goods_form = GoodsForm(request.POST, application=application)

            if goods_form.is_valid():
                obj = goods_form.save(commit=False)
                obj.import_application = application
                obj.save()

                return redirect(
                    reverse("import:sanctions:edit", kwargs={"application_pk": application_pk})
                )
        else:
            goods_form = GoodsForm(application=application)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": goods_form,
            "page_title": "Sanctions and Adhoc License Application",
            "commodity_group_data": _get_sanctions_commodity_group_data(application),
            "case_type": "import",
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

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        goods = get_object_or_404(application.sanctionsandadhocapplicationgoods_set, pk=goods_pk)
        if request.POST:
            form = GoodsForm(request.POST, instance=goods, application=application)

            if form.is_valid():
                obj = form.save(commit=False)
                obj.import_application = application
                obj.save()

                return redirect(
                    reverse("import:sanctions:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = GoodsForm(instance=goods, application=application)

        commodity_group_data = _get_sanctions_commodity_group_data(application)
        unit_label = get_commodity_unit(commodity_group_data, goods.commodity)

        context = {
            "case_type": "import",
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Edit Goods",
            "commodity_group_data": commodity_group_data,
            "unit_label": unit_label,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/sanctions/add_or_edit_goods.html", context)


def _get_sanctions_commodity_group_data(application):
    usage_records = get_usage_records(
        ImportApplicationType.Types.SANCTION_ADHOC  # type: ignore[arg-type]
    ).filter(country=application.origin_country)

    return get_commodity_group_data(usage_records)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_goods_licence(
    request: AuthenticatedHttpRequest, *, application_pk: int, goods_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, "import", Task.TaskType.PROCESS)

        goods = get_object_or_404(application.sanctionsandadhocapplicationgoods_set, pk=goods_pk)

        if request.POST:
            form = GoodsSanctionsLicenceForm(request.POST, instance=goods)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application.pk, "case_type": "import"},
                    )
                )
        else:
            form = GoodsSanctionsLicenceForm(instance=goods)

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
            "web/domains/case/import/manage/response-prep-edit-form.html",
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

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

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
            "case_type": "import",
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

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

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

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:sanctions:edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(
            SanctionsAndAdhocLicenseForm(data=model_to_dict(application), instance=application),
            page_errors,
        )

        # check all commodities are valid
        goods_commodities = SanctionsAndAdhocApplicationGoods.objects.filter(
            import_application=application
        ).values_list("commodity__commodity_code", flat=True)

        if goods_commodities.count() == 0:
            page_errors.add(
                FieldError(
                    field_name="Commodity List",
                    messages=["Please ensure you have added at least one commodity."],
                )
            )

        usage_records = get_usage_records(
            ImportApplicationType.Types.SANCTION_ADHOC  # type: ignore[arg-type]
        ).filter(country=application.origin_country)

        sanction_and_adhoc_commodities = get_usage_commodities(usage_records).values_list(
            "commodity_code", flat=True
        )

        for goods_commodity in goods_commodities:
            if goods_commodity not in sanction_and_adhoc_commodities:
                page_errors.add(
                    FieldError(
                        field_name="Goods - Commodity Code",
                        messages=[
                            f"Commodity '{goods_commodity}' is invalid for the selected country of origin."
                        ],
                    )
                )

        errors.add(page_errors)

        errors.add(get_org_update_request_errors(application, "import"))

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
        "case_type": "import",
    }
    return render(request, "web/domains/case/import/import-case-submit.html", context)
