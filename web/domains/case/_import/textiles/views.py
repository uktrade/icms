from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.views import (
    check_application_permission,
    get_application_current_task,
    view_application_file,
)
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.types import AuthenticatedHttpRequest
from web.utils.commodity import get_category_commodity_group_data
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .forms import (
    EditTextilesForm,
    GoodsTextilesLicenceForm,
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

        task = get_application_current_task(application, "import", "prepare")

        if request.POST:
            form = EditTextilesForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:textiles:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditTextilesForm(instance=application, initial={"contact": request.user})

        supporting_documents = application.supporting_documents.filter(is_active=True)
        category_commodity_groups = get_category_commodity_group_data(commodity_type="TEXTILES")

        if application.category_commodity_group:
            selected_group = category_commodity_groups.get(
                application.category_commodity_group.pk, {}
            )
        else:
            selected_group = {}

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Textiles (Quota) Import Licence - Edit",
            "supporting_documents": supporting_documents,
            "category_commodity_groups": category_commodity_groups,
            "commodity_group_label": selected_group.get("label", ""),
            "commodity_group_unit": selected_group.get("unit", ""),
        }

        return render(request, "web/domains/case/import/textiles/edit.html", context)


@login_required
def submit_textiles(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", "prepare")

        errors = ApplicationErrors()

        edit_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:textiles:edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(
            EditTextilesForm(data=model_to_dict(application), instance=application), edit_errors
        )
        errors.add(edit_errors)

        errors.add(get_org_update_request_errors(application, "import"))

        if request.POST:
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
            "page_title": "Textiles (Quota) Import Licence - Submit",
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/textiles/submit.html", context)


@login_required
def add_document(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", "prepare")

        if request.POST:
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
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Textiles (Quota) Import Licence - Add supporting document",
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

        get_application_current_task(application, "import", "prepare")

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:textiles:edit", kwargs={"application_pk": application_pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )
        task = get_application_current_task(application, "import", "process")
        checklist, created = TextilesChecklist.objects.get_or_create(import_application=application)

        if request.POST:
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
                form = TextilesChecklistForm(instance=checklist)
            else:
                form = TextilesChecklistForm(data=model_to_dict(checklist), instance=checklist)

        context = {
            "process": application,
            "task": task,
            "page_title": "Textiles (Quota) Import Licence - Checklist",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_goods_licence(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, "import", "process")

        if request.POST:
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
            "task": task,
            "page_title": "Edit Goods",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/response-prep-textiles-edit-form.html",
            context=context,
        )
