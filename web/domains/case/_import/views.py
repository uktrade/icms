from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render, reverse
from django.views.generic import TemplateView

from web.domains.case._import.forms import CreateOILForm
from web.domains.case._import.models import OpenIndividualLicenceApplication
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
    # TODO: next step when creating OIL Application
    return render(request, "web/domains/case/import/firearms/oil/edit.html", {})
