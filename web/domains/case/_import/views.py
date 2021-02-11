from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render, reverse
from django.views.generic import TemplateView

from web.flow.models import Task

from .firearms.models import OpenIndividualLicenceApplication
from .forms import CreateImportApplicationForm
from .models import ImportApplicationType
from .sanctions.models import SanctionsAndAdhocApplication


class ImportApplicationChoiceView(TemplateView, PermissionRequiredMixin):
    template_name = "web/domains/case/import/choice.html"
    permission_required = "web.importer_access"


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_sanctions(request):
    import_application_type = ImportApplicationType.TYPE_SANCTION_ADHOC
    model_class = SanctionsAndAdhocApplication
    redirect_view = "import:sanctions-applicant-details"
    return _create_application(request, import_application_type, model_class, redirect_view)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_oil(request):
    import_application_type = ImportApplicationType.SUBTYPE_OPEN_INDIVIDUAL_LICENCE
    model_class = OpenIndividualLicenceApplication
    redirect_view = "import:edit-oil"
    return _create_application(request, import_application_type, model_class, redirect_view)


def _create_application(request, import_application_type, model_class, redirect_view):
    import_application_type = ImportApplicationType.objects.get(
        Q(type=import_application_type) | Q(sub_type=import_application_type)
    )

    with transaction.atomic():
        if request.POST:
            form = CreateImportApplicationForm(request.user, request.POST)
            if form.is_valid():
                application = model_class()
                application.importer = form.cleaned_data["importer"]
                application.importer_office = form.cleaned_data["importer_office"]
                application.process_type = model_class.PROCESS_TYPE
                application.created_by = request.user
                application.last_updated_by = request.user
                application.submitted_by = request.user
                application.application_type = import_application_type
                application.save()
                Task.objects.create(process=application, task_type="prepare", owner=request.user)
                return redirect(reverse(redirect_view, kwargs={"pk": application.pk}))
        else:
            form = CreateImportApplicationForm(request.user)

        context = {"form": form, "import_application_type": import_application_type}
        return render(request, "web/domains/case/import/create.html", context)
