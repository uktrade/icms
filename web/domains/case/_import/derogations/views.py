from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.utils import (
    check_application_permission,
    get_application_current_task,
)
from web.domains.country.models import Country
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .. import views as import_views
from .forms import (
    DerogationsChecklistForm,
    DerogationsChecklistOptionalForm,
    DerogationsForm,
    DerogationsSyriaChecklistForm,
    DerogationsSyriaChecklistOptionalForm,
    GoodsDerogationsLicenceForm,
)
from .models import DerogationsApplication, DerogationsChecklist


@login_required
def edit_derogations(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        syria = Country.objects.get(name="Syria")

        if request.method == "POST":
            form = DerogationsForm(data=request.POST, instance=application)

            if form.is_valid():
                application = form.save(commit=False)

                # Clear the syria section if needed
                if syria not in (application.origin_country, application.consignment_country):
                    application.entity_consulted_name = None
                    application.activity_benefit_anyone = None
                    application.purpose_of_request = None
                    application.civilian_purpose_details = None

                application.save()

                return redirect(
                    reverse("import:derogations:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DerogationsForm(instance=application, initial={"contact": request.user})

        supporting_documents = application.supporting_documents.filter(is_active=True)

        show_fd = syria in (application.origin_country, application.consignment_country)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": get_page_title("Edit"),
            "supporting_documents": supporting_documents,
            "show_further_details": show_fd,
        }

        return render(request, "web/domains/case/import/derogations/edit.html", context)


@login_required
def add_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        if request.POST:
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:derogations:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": get_page_title("Add supporting document"),
        }

        return render(
            request, "web/domains/case/import/derogations/add_supporting_document.html", context
        )


@require_GET
@login_required
def view_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: DerogationsApplication = get_object_or_404(
        DerogationsApplication, pk=application_pk
    )

    return import_views.view_file(
        request, application, application.supporting_documents, document_pk
    )


@require_POST
@login_required
def delete_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse("import:derogations:edit", kwargs={"application_pk": application_pk})
        )


@login_required
def submit_derogations(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        errors = _get_derogations_errors(application)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                # TODO: replace with Endorsement Usage Template (ICMSLST-638)
                # endorsements are active on ICMS1 but inactive in our db
                # first_endorsement = Template.objects.get(
                #     is_active=True,
                #     template_type=Template.ENDORSEMENT,
                #     template_name="Endorsement 1 (must be updated each year)",
                # )
                # application.endorsements.create(content=first_endorsement.template_content)
                # second_endorsement = Template.objects.get(
                #     is_active=True,
                #     template_type=Template.ENDORSEMENT,
                #     template_name="Endorsement 15",
                # )
                # application.endorsements.create(content=second_endorsement.template_content)

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
            "page_title": get_page_title("Submit"),
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/derogations/submit.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )
        task = get_application_current_task(application, "import", Task.TaskType.PROCESS)
        checklist, created = DerogationsChecklist.objects.get_or_create(
            import_application=application
        )

        syria = Country.objects.get(name="Syria")
        include_extra = syria in (application.origin_country, application.consignment_country)

        if include_extra:
            checklist_form = DerogationsSyriaChecklistForm
            checklist_optional_form = DerogationsSyriaChecklistOptionalForm
        else:
            checklist_form = DerogationsChecklistForm
            checklist_optional_form = DerogationsChecklistOptionalForm

        if request.POST:
            form: DerogationsChecklistForm = checklist_optional_form(
                request.POST, instance=checklist
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:derogations:manage-checklist",
                        kwargs={"application_pk": application_pk},
                    )
                )
        else:
            if created:
                form = checklist_form(instance=checklist)
            else:
                form = checklist_form(data=model_to_dict(checklist), instance=checklist)

        context = {
            "process": application,
            "task": task,
            "page_title": get_page_title("Checklist"),
            "form": form,
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
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, "import", Task.TaskType.PROCESS)

        if request.POST:
            form = GoodsDerogationsLicenceForm(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = GoodsDerogationsLicenceForm(instance=application)

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Edit Goods",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/response-prep-edit-form.html",
            context=context,
        )


def get_page_title(page: str) -> str:
    return f"Derogation from Sanctions Import Ban - {page}"


def _get_derogations_errors(application: DerogationsApplication) -> ApplicationErrors:
    errors = ApplicationErrors()

    page_errors = PageErrors(
        page_name="Application details",
        url=reverse("import:derogations:edit", kwargs={"application_pk": application.pk}),
    )
    create_page_errors(
        DerogationsForm(data=model_to_dict(application), instance=application), page_errors
    )
    errors.add(page_errors)

    if not application.supporting_documents.filter(is_active=True).exists():
        supporting_document_errors = PageErrors(
            page_name="Supporting Documents",
            url=reverse(
                "import:derogations:add-supporting-document",
                kwargs={"application_pk": application.pk},
            ),
        )
        supporting_document_errors.add(
            FieldError(
                field_name="Provide details of why this is a pre-existing contract",
                messages=["Please ensure you have uploaded at least one supporting document."],
            )
        )

        errors.add(supporting_document_errors)

    errors.add(get_org_update_request_errors(application, "import"))

    return errors
