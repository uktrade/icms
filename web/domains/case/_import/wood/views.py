from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse

from web.domains.case._import.models import ImportApplication

from .forms import PrepareWoodQuotaForm
from .models import WoodQuotaApplication


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_wood_quota(request, pk):
    with transaction.atomic():
        application = get_object_or_404(WoodQuotaApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = PrepareWoodQuotaForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(reverse("import:edit-wood-quota", kwargs={"pk": pk}))

        else:
            form = PrepareWoodQuotaForm(instance=application, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Wood (Quota) Import Licence",
        }

        return render(request, "web/domains/case/import/wood/edit.html", context)
