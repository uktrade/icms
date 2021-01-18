from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.generic import TemplateView

from web.domains.case._import.forms import CreateOILForm, PrepareOILForm
from web.domains.case._import.models import (
    ImportApplication,
    OpenIndividualLicenceApplication,
)
from web.flow.models import Task


class ImportApplicationChoiceView(TemplateView, PermissionRequiredMixin):
    template_name = "web/domains/case/import/choice.html"
    permission_required = "web.importer_access"


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_oil(request):
    with transaction.atomic():
        if request.POST:
            form = CreateOILForm(request.user, request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.process_type = OpenIndividualLicenceApplication.PROCESS_TYPE
                application.created_by = request.user
                application.last_updated_by = request.user
                application.submitted_by = request.user
                application.save()

                Task.objects.create(process=application, task_type="prepare", owner=request.user)
                return redirect(reverse("edit-oil", kwargs={"pk": application.pk}))
        else:
            form = CreateOILForm(request.user)

        context = {"form": form, "page_title": "Open Individual Import Licence"}
        return render(request, "web/domains/case/import/firearms/oil/create.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_oil(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = PrepareOILForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(reverse("edit-oil", kwargs={"pk": pk}))

        else:
            form = PrepareOILForm(instance=application, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence",
        }

        return render(request, "web/domains/case/import/firearms/oil/edit.html", context)
