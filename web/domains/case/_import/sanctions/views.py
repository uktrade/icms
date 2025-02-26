import logging
from collections import Counter
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.services import case_progress
from web.domains.case.utils import (
    get_application_form,
    redirect_after_submit,
    submit_application,
    view_application_file,
)
from web.domains.file.utils import create_file_model
from web.domains.template.utils import add_template_data_on_submit
from web.models import Country, ImportApplicationType, Task, User
from web.permissions import AppChecker, Perms
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

from .forms import (
    EditSanctionsAndAdhocLicenceForm,
    GoodsForm,
    GoodsSanctionsLicenceForm,
    SubmitSanctionsAndAdhocLicenceForm,
)
from .models import SanctionsAndAdhocApplication, SanctionsAndAdhocApplicationGoods

logger = logging.getLogger(__name__)


def check_can_edit_application(user: User, application: SanctionsAndAdhocApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


@login_required
def edit_application(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        form = get_application_form(
            application,
            request,
            EditSanctionsAndAdhocLicenceForm,
            SubmitSanctionsAndAdhocLicenceForm,
        )

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:sanctions:edit", kwargs={"application_pk": application_pk})
                )

        supporting_documents = application.supporting_documents.filter(is_active=True)
        context = {
            "process": application,
            "form": form,
            "page_title": "Sanctions and Adhoc Licence Application - Edit",
            "supporting_documents": supporting_documents,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/sanctions/edit_application.html", context)


class SanctionsGoodsDetailView(
    LoginRequiredMixin, case_progress.InProgressApplicationStatusTaskMixin, DetailView
):
    http_method_names = ["get"]
    template_name = "web/domains/case/import/sanctions/goods-list.html"

    # Extra typing for clarity
    application: SanctionsAndAdhocApplication

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        goods_list = annotate_commodity_unit(
            self.application.sanctions_goods.all(), "commodity__"
        ).distinct()

        # Check if the main application is valid when showing add goods link
        show_add_goods = SubmitSanctionsAndAdhocLicenceForm(
            instance=self.application, data=model_to_dict(self.application)
        ).is_valid()

        return context | {
            "process": self.application,
            "page_title": "Sanctions and Adhoc Licence Application - Goods",
            "goods_list": goods_list,
            "show_add_goods": show_add_goods,
            "case_type": "import",
        }


@login_required
def add_goods(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        if request.method == "POST":
            goods_form = GoodsForm(request.POST, application=application)

            if goods_form.is_valid():
                obj: SanctionsAndAdhocApplicationGoods = goods_form.save(commit=False)
                obj.import_application = application
                obj.goods_description_original = obj.goods_description
                obj.quantity_amount_original = obj.quantity_amount
                obj.value_original = obj.value
                obj.save()

                return redirect(
                    reverse(
                        "import:sanctions:list-goods", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            goods_form = GoodsForm(application=application)

        context = {
            "process": application,
            "form": goods_form,
            "page_title": "Sanctions and Adhoc Licence Application - Add Goods",
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

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        goods = get_object_or_404(application.sanctions_goods, pk=goods_pk)
        if request.method == "POST":
            form = GoodsForm(request.POST, instance=goods, application=application)

            if form.is_valid():
                obj: SanctionsAndAdhocApplicationGoods = form.save(commit=False)
                obj.import_application = application
                obj.goods_description_original = obj.goods_description
                obj.quantity_amount_original = obj.quantity_amount
                obj.value_original = obj.value
                obj.save()

                return redirect(
                    reverse(
                        "import:sanctions:list-goods", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            form = GoodsForm(instance=goods, application=application)

        commodity_group_data = _get_sanctions_commodity_group_data(application)
        unit_label = get_commodity_unit(commodity_group_data, goods.commodity)

        context = {
            "case_type": "import",
            "process": application,
            "form": form,
            "page_title": "Sanctions and Adhoc Licence Application - Edit Goods",
            "commodity_group_data": commodity_group_data,
            "unit_label": unit_label,
        }

        return render(request, "web/domains/case/import/sanctions/add_or_edit_goods.html", context)


def _get_sanctions_commodity_group_data(application):
    usage_records = get_usage_records(ImportApplicationType.Types.SANCTION_ADHOC).filter(
        country=application.origin_country
    )

    return get_commodity_group_data(usage_records)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_goods_licence(
    request: AuthenticatedHttpRequest, *, application_pk: int, goods_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        goods = get_object_or_404(application.sanctions_goods, pk=goods_pk)

        if request.method == "POST":
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
            "process": application,
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def reset_goods_licence(
    request: AuthenticatedHttpRequest, *, application_pk: int, goods_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: SanctionsAndAdhocApplication = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        goods = get_object_or_404(application.sanctions_goods, pk=goods_pk)
        goods.goods_description = goods.goods_description_original
        goods.quantity_amount = goods.quantity_amount_original
        goods.value = goods.value_original
        goods.save()

        return redirect(
            reverse(
                "case:prepare-response",
                kwargs={"application_pk": application.pk, "case_type": "import"},
            )
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

        check_can_edit_application(request.user, application)

        get_object_or_404(application.sanctions_goods, pk=goods_pk).delete()

    return redirect(
        reverse("import:sanctions:list-goods", kwargs={"application_pk": application_pk})
    )


class SanctionsSupportingDocumentsDetailView(
    LoginRequiredMixin, case_progress.InProgressApplicationStatusTaskMixin, DetailView
):
    http_method_names = ["get"]
    template_name = "web/domains/case/import/sanctions/supporting-documents-list.html"

    # Extra typing for clarity
    application: SanctionsAndAdhocApplication

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        supporting_documents = self.application.supporting_documents.filter(is_active=True)

        return context | {
            "process": self.application,
            "page_title": "Sanctions and Adhoc Licence Application - Supporting Documents",
            "supporting_documents": supporting_documents,
            "case_type": "import",
        }


@login_required
def add_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = DocumentForm(request.POST, request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse(
                        "import:sanctions:list-documents", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            form = DocumentForm()

        context = {
            "process": application,
            "form": form,
            "page_title": "Sanctions and Adhoc Licence Application",
            "case_type": "import",
        }
        return render(request, "web/domains/case/import/sanctions/add_document.html", context)


@require_GET
@login_required
def view_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(SanctionsAndAdhocApplication, pk=application_pk)

    return view_application_file(
        request.user, application, application.supporting_documents, document_pk
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

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse("import:sanctions:list-documents", kwargs={"application_pk": application_pk})
        )


@login_required
def submit_sanctions(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        edit_url = reverse("import:sanctions:edit", kwargs={"application_pk": application.pk})
        edit_url = f"{edit_url}?validate"
        add_goods_url = reverse(
            "import:sanctions:add-goods", kwargs={"application_pk": application.pk}
        )

        page_errors = PageErrors(page_name="Application Details", url=edit_url)
        create_page_errors(
            SubmitSanctionsAndAdhocLicenceForm(
                data=model_to_dict(application), instance=application
            ),
            page_errors,
        )

        # check all commodities are valid
        goods_commodities = SanctionsAndAdhocApplicationGoods.objects.filter(
            import_application=application
        ).values_list("commodity__commodity_code", flat=True)

        if goods_commodities.count() == 0:
            goods_errors = PageErrors(page_name="Application Details - Goods", url=add_goods_url)
            goods_errors.add(
                FieldError(field_name="Goods", messages=["At least one goods line must be added"])
            )
        else:
            goods_errors = None

        sanctioned_countries = Country.app.get_sanctions_countries()

        countries_to_search = []
        if application.origin_country in sanctioned_countries:
            countries_to_search.append(application.origin_country)

        if application.consignment_country in sanctioned_countries:
            countries_to_search.append(application.consignment_country)

        usage_records = get_usage_records(ImportApplicationType.Types.SANCTION_ADHOC).filter(
            country__in=countries_to_search
        )

        sanction_and_adhoc_commodities = get_usage_commodities(usage_records).values_list(
            "commodity_code", flat=True
        )

        for goods_commodity in goods_commodities:
            if goods_commodity not in sanction_and_adhoc_commodities:
                page_errors.add(
                    FieldError(
                        field_name="Goods - Commodity Code",
                        messages=[
                            f"Commodity '{goods_commodity}' is invalid for the selected country of manufacture or country of shipment."
                        ],
                    )
                )

        # Check for duplicate commodities
        goods = Counter(goods_commodities)
        duplicate_commodities = [commodity for commodity, count in goods.items() if count > 1]

        if duplicate_commodities:
            duplicates = ", ".join(duplicate_commodities)

            page_errors.add(
                FieldError(
                    field_name="Goods - Commodity Code",
                    messages=[
                        f"Duplicate commodity codes. Please ensure these codes are only listed once: {duplicates}."
                    ],
                )
            )

        errors.add(page_errors)

        if goods_errors:
            errors.add(goods_errors)

        errors.add(get_org_update_request_errors(application, "import"))

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                submit_application(application, request, task)
                add_template_data_on_submit(application)

                return redirect_after_submit(application)

        else:
            form = SubmitForm()

    context = {
        "page_title": "Sanctions and Adhoc Licence Application - Submit Application",
        "process": application,
        "form": form,
        "application_title": "Sanctions and Adhoc Licence Application",
        "declaration": application.application_type.declaration_template,
        "errors": errors if errors.has_errors() else None,
        "case_type": "import",
    }
    return render(request, "web/domains/case/import/import-case-submit.html", context)
