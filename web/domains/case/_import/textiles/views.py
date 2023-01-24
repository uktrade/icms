from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.services import case_progress
from web.domains.case.utils import (
    check_application_permission,
    get_application_current_task,
    get_application_form,
    redirect_after_submit,
    submit_application,
    view_application_file,
)
from web.domains.case.views.utils import get_current_task_and_readonly_status
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.commodity import (
    get_category_commodity_group_data,
    get_usage_data,
    get_usage_records,
)
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from ..models import ImportApplicationType
from .forms import (
    EditTextilesForm,
    GoodsTextilesLicenceForm,
    SubmitTextilesForm,
    TextilesChecklistForm,
    TextilesChecklistOptionalForm,
)
from .models import TextilesApplication, TextilesChecklist


@login_required
def edit_textiles(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        form = get_application_form(application, request, EditTextilesForm, SubmitTextilesForm)

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:textiles:edit", kwargs={"application_pk": application_pk})
                )

        supporting_documents = application.supporting_documents.filter(is_active=True)
        category_commodity_groups = get_category_commodity_group_data(commodity_type="TEXTILES")
        usages = get_usage_data(app_type=ImportApplicationType.Types.TEXTILES)  # type: ignore[arg-type]

        if application.category_commodity_group:
            selected_group = category_commodity_groups.get(
                application.category_commodity_group.pk, {}
            )
        else:
            selected_group = {}

        context = {
            "process": application,
            "form": form,
            "page_title": "Textiles (Quota) Import Licence - Edit",
            "supporting_documents": supporting_documents,
            "category_commodity_groups": category_commodity_groups,
            "commodity_group_label": selected_group.get("label", ""),
            "commodity_group_unit": selected_group.get("unit", ""),
            "usages": usages,
            "max_allocation": _get_max_allocation(application),
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/textiles/edit.html", context)


@login_required
def submit_textiles(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        edit_url = reverse("import:textiles:edit", kwargs={"application_pk": application.pk})
        edit_url = f"{edit_url}?validate"

        edit_errors = PageErrors(page_name="Application details", url=edit_url)
        create_page_errors(
            SubmitTextilesForm(data=model_to_dict(application), instance=application), edit_errors
        )
        errors.add(edit_errors)

        errors.add(get_org_update_request_errors(application, "import"))

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                endorsement = Template.objects.get(
                    template_name="Endorsement 1 (must be updated each year)",
                    template_type=Template.ENDORSEMENT,
                    application_domain="IMA",
                )
                application.endorsements.create(content=endorsement.template_content)
                application.category_licence_description = (
                    application.category_commodity_group.group_description
                )
                submit_application(application, request, task)

                return redirect_after_submit(application, request)

        else:
            form = SubmitForm()

        declaration = Template.objects.filter(
            is_active=True,
            template_type=Template.DECLARATION,
            application_domain=Template.IMPORT_APPLICATION,
            template_code="IMA_GEN_DECLARATION",
        ).first()

        context = {
            "process": application,
            "form": form,
            "page_title": "Textiles (Quota) Import Licence - Submit",
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
            "max_allocation": _get_max_allocation(application),
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/textiles/submit.html", context)


@login_required
def add_document(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:textiles:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process": application,
            "form": form,
            "page_title": "Textiles (Quota) Import Licence - Add supporting document",
            "case_type": "import",
        }

        return render(
            request, "web/domains/case/import/textiles/add_supporting_document.html", context
        )


@require_GET
@login_required
def view_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: TextilesApplication = get_object_or_404(TextilesApplication, pk=application_pk)

    return view_application_file(
        request.user, application, application.supporting_documents, document_pk, "import"
    )


@require_POST
@login_required
def delete_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:textiles:edit", kwargs={"application_pk": application_pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )
        _, readonly_view = get_current_task_and_readonly_status(
            application, "import", request.user, Task.TaskType.PROCESS
        )
        checklist, created = TextilesChecklist.objects.get_or_create(import_application=application)

        if request.method == "POST" and not readonly_view:
            form: TextilesChecklistForm = TextilesChecklistOptionalForm(
                request.POST, instance=checklist
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:textiles:manage-checklist",
                        kwargs={"application_pk": application_pk},
                    )
                )
        else:
            if created:
                form = TextilesChecklistForm(instance=checklist, readonly_form=readonly_view)
            else:
                form = TextilesChecklistForm(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": "Textiles (Quota) Import Licence - Checklist",
            "form": form,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_goods_licence(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, "import", Task.TaskType.PROCESS)

        if request.method == "POST":
            form = GoodsTextilesLicenceForm(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application.pk, "case_type": "import"},
                    )
                )
        else:
            form = GoodsTextilesLicenceForm(instance=application)

        context = {
            "case_type": "import",
            "process": application,
            "page_title": "Edit Goods",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/response-prep-textiles-edit-form.html",
            context=context,
        )


def _get_max_allocation(application: TextilesApplication) -> float:
    if application.category_commodity_group and application.origin_country:
        usages = (
            get_usage_records(app_type=ImportApplicationType.Types.TEXTILES)  # type: ignore[arg-type]
            .filter(
                commodity_group=application.category_commodity_group,
                country=application.origin_country,
            )
            .exclude(maximum_allocation__isnull=True)
        )
        latest = usages.last()
        max_allocation = latest.maximum_allocation if latest else None
    else:
        max_allocation = None

    return max_allocation
