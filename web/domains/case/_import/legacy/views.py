from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from web.domains.case.utils import view_application_file
from web.domains.case.views.utils import get_caseworker_view_readonly_status
from web.models import (
    OPTChecklist,
    OutwardProcessingTradeApplication,
    TextilesApplication,
    TextilesChecklist,
)
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest

from .forms import (
    OPTChecklistForm,
    OPTChecklistOptionalForm,
    TextilesChecklistForm,
    TextilesChecklistOptionalForm,
)


@require_GET
@login_required
def opt_view_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: OutwardProcessingTradeApplication = get_object_or_404(
        OutwardProcessingTradeApplication, pk=application_pk
    )

    return view_application_file(request.user, application, application.documents, document_pk)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def opt_manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )
        readonly_view = get_caseworker_view_readonly_status(application, "import", request.user)

        checklist, created = OPTChecklist.objects.get_or_create(import_application=application)

        if request.method == "POST" and not readonly_view:
            form: OPTChecklistForm = OPTChecklistOptionalForm(request.POST, instance=checklist)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:legacy:opt-manage-checklist",
                        kwargs={"application_pk": application_pk},
                    )
                )
        else:
            if created:
                form = OPTChecklistForm(instance=checklist, readonly_form=readonly_view)
            else:
                form = OPTChecklistForm(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": "Outward Processing Trade Licence - Checklist",
            "form": form,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )


@require_GET
@login_required
def tex_view_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: TextilesApplication = get_object_or_404(TextilesApplication, pk=application_pk)

    return view_application_file(
        request.user, application, application.supporting_documents, document_pk
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def tex_manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )
        readonly_view = get_caseworker_view_readonly_status(application, "import", request.user)
        checklist, created = TextilesChecklist.objects.get_or_create(import_application=application)

        if request.method == "POST" and not readonly_view:
            form: TextilesChecklistForm = TextilesChecklistOptionalForm(
                request.POST, instance=checklist
            )

            if form.is_valid():
                form.save()
                return redirect(
                    reverse(
                        "import:legacy:tex-manage-checklist",
                        kwargs={"application_pk": application_pk},
                    )
                )
        else:
            if created:
                form = TextilesChecklistForm(instance=checklist, readonly_form=readonly_view)
            else:
                form = TextilesChecklistForm(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": "Textiles (Quota) Import Licence - Checklist",
            "form": form,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )
