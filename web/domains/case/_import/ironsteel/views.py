from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from web.domains.case._import.models import ImportApplication
from web.domains.case.views import check_application_permission
from web.types import AuthenticatedHttpRequest

from .forms import EditIronSteelForm
from .models import IronSteelApplication


@login_required
def edit_ironsteel(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: IronSteelApplication = get_object_or_404(
            IronSteelApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = EditIronSteelForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:ironsteel:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditIronSteelForm(instance=application, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Iron and Steel (Quota) Import Licence - Edit",
        }

        return render(request, "web/domains/case/import/ironsteel/edit.html", context)


@login_required
def submit_ironsteel(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    # TODO: implement (ICMSLST-885)
    raise NotImplementedError
