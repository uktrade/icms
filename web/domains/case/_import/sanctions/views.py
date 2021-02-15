import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, render

from web.domains.case._import.models import ImportApplication

from .models import SanctionsAndAdhocApplication

logger = logging.getLogger(__name__)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def sanctions_show_applicant_details(request, pk):

    # Transaction atomic required as get_task performs select for update
    application = get_object_or_404(SanctionsAndAdhocApplication.objects, pk=pk)
    with transaction.atomic():
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "task": task,
        "application_title": "Sanctions and Adhoc License Application",
    }
    return render(
        request, "web/domains/case/import/sanctions/sanctions_show_applicant_details.html", context
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def sanctions_and_adhoc_licence_application_details(request, pk):
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
        request,
        "web/domains/case/import/sanctions/sanctions_and_adhoc_licence_application_details.html",
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
