from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone

from web.domains.case._import.models import ImportApplication
from web.domains.template.models import Template
from web.flow.models import Task
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .forms import DerogationsForm, SubmitDerogationsForm
from .models import DerogationsApplication


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_derogations(request, pk):
    with transaction.atomic():
        application = get_object_or_404(DerogationsApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.method == "POST":
            form = DerogationsForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(reverse("import:derogations:edit-derogations", kwargs={"pk": pk}))
        else:
            form = DerogationsForm(instance=application, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Derogation from Sanctions Import Ban - Edit",
        }

        return render(request, "web/domains/case/import/derogations/edit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def submit_derogations(request, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(DerogationsApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        errors = ApplicationErrors()

        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:derogations:edit-derogations", kwargs={"pk": pk}),
        )
        create_page_errors(
            DerogationsForm(data=model_to_dict(application), instance=application), page_errors
        )
        errors.add(page_errors)

        if request.POST:
            form = SubmitDerogationsForm(data=request.POST)

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
            form = SubmitDerogationsForm()

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
            "page_title": "Derogation from Sanctions Import Ban - Submit",
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/derogations/submit.html", context)
