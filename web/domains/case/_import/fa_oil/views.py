from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import SubmitForm
from web.domains.template.models import Template
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .forms import (
    ChecklistFirearmsOILApplicationForm,
    ChecklistFirearmsOILApplicationOptionalForm,
    PrepareOILForm,
)
from .models import ChecklistFirearmsOILApplication, OpenIndividualLicenceApplication


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_oil(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = PrepareOILForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:fa-oil:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = PrepareOILForm(instance=application, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence - Edit",
        }

        return render(request, "web/domains/case/import/fa-oil/edit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def submit_oil(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        errors = ApplicationErrors()

        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:fa-oil:edit", kwargs={"application_pk": pk}),
        )
        create_page_errors(
            PrepareOILForm(data=model_to_dict(application), instance=application), page_errors
        )
        errors.add(page_errors)

        has_certificates = (
            application.user_imported_certificates.filter(is_active=True).exists()
            or application.verified_certificates.filter(is_active=True).exists()
        )

        if not has_certificates:
            page_errors = PageErrors(
                page_name="Certificates",
                url=reverse("import:fa:manage-certificates", kwargs={"application_pk": pk}),
            )

            page_errors.add(
                FieldError(
                    field_name="Certificate", messages=["At least one certificate must be added"]
                )
            )

            errors.add(page_errors)

        if application.know_bought_from and not application.importcontact_set.exists():
            page_errors = PageErrors(
                page_name="Details of who bought from",
                url=reverse("import:fa:list-import-contacts", kwargs={"application_pk": pk}),
            )

            page_errors.add(
                FieldError(field_name="Person", messages=["At least one person must be added"])
            )

            errors.add(page_errors)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                template = Template.objects.get(template_code="COVER_FIREARMS_OIL")
                application.cover_letter = template.get_content(
                    {
                        "CONTACT_NAME": application.contact,
                        "APPLICATION_SUBMITTED_DATE": application.submit_datetime,
                    }
                )
                application.save()

                # TODO: replace with Endorsement Usage Template (ICMSLST-638)
                endorsement = Template.objects.get(
                    is_active=True,
                    template_type=Template.ENDORSEMENT,
                    template_name="Open Individual Licence endorsement",
                )
                application.endorsements.create(content=endorsement.template_content)

                return redirect(reverse("home"))

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
            "page_title": "Open Individual Import Licence - Submit Application",
            "form": form,
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/fa-oil/submit.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OpenIndividualLicenceApplication = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.Statuses.SUBMITTED, "process")
        checklist, created = ChecklistFirearmsOILApplication.objects.get_or_create(
            import_application=application
        )

        if request.POST:
            form: ChecklistFirearmsOILApplicationForm = ChecklistFirearmsOILApplicationOptionalForm(
                request.POST, instance=checklist
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa-oil:manage-checklist", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            if created:
                form = ChecklistFirearmsOILApplicationForm(instance=checklist)
            else:
                form = ChecklistFirearmsOILApplicationForm(
                    data=model_to_dict(checklist), instance=checklist
                )

        context = {
            "process": application,
            "task": task,
            "page_title": "Open Individual Import Licence - Checklist",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )
