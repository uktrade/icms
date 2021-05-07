from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from web.domains.case._import.models import ImportApplication

from .forms import PrepareDFLForm
from .models import DFLApplication


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_dlf(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(DFLApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = PrepareDFLForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()
                return redirect(reverse("import:fa-dfl:edit", kwargs={"pk": pk}))

        else:
            form = PrepareDFLForm(
                instance=application,
                # This will be needed when doing the rest of the form
                # initial={"contact": request.user}
            )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms and Ammunition (Deactivated Firearms Licence) - Edit",
        }

        return render(request, "web/domains/case/import/fa-dfl/edit.html", context)
