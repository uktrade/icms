import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse

from web.domains.case._import.models import ImportApplication

from .forms import SanctionsAndAdhocLicenseForm
from .models import SanctionsAndAdhocApplication

logger = logging.getLogger(__name__)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_sanctions_and_adhoc_licence_application(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.method == "POST":
            form = SanctionsAndAdhocLicenseForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:edit-sanctions-and-adhoc-licence-application", kwargs={"pk": pk}
                    )
                )

        else:
            form = SanctionsAndAdhocLicenseForm(
                instance=application, initial={"contact": request.user}
            )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Sanctions and Adhoc License Application",
        }
        return render(
            request,
            "web/domains/case/import/sanctions/edit_sanctions_and_adhoc_licence_application.html",
            context,
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def sanctions_validation_summary(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "task": task,
        "application_title": "Sanctions and Adhoc License Application",
    }
    return render(
        request, "web/domains/case/import/sanctions/sanctions_validation_summary.html", context
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def sanctions_application_submit(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            SanctionsAndAdhocApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "task": task,
        "application_title": "Sanctions and Adhoc License Application",
    }
    return render(
        request, "web/domains/case/import/sanctions/sanctions_application_submit.html", context
    )
