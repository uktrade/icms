from typing import Optional, Type, Union

import django.forms as django_forms
import weasyprint
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3

from .derogations.models import DerogationsApplication
from .fa_dfl.models import DFLApplication
from .fa_oil.models import OpenIndividualLicenceApplication
from .fa_sil.models import SILApplication
from .forms import (
    CoverLetterForm,
    CreateImportApplicationForm,
    CreateWoodQuotaApplicationForm,
    EndorsementChoiceImportApplicationForm,
    EndorsementImportApplicationForm,
    LicenceDateAndPaperLicenceForm,
    LicenceDateForm,
    OPTLicenceForm,
)
from .models import ImportApplication, ImportApplicationType
from .opt.models import OutwardProcessingTradeApplication
from .sanctions.models import SanctionsAndAdhocApplication
from .sps.models import PriorSurveillanceApplication
from .textiles.models import TextilesApplication
from .wood.models import WoodQuotaApplication


class ImportApplicationChoiceView(PermissionRequiredMixin, TemplateView):
    template_name = "web/domains/case/import/choose.html"
    permission_required = "web.importer_access"

    def get_context_data(self):
        context = super().get_context_data()

        show_opt = ImportApplicationType.objects.get(type=ImportApplicationType.Types.OPT).is_active

        show_textiles = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.TEXTILES
        ).is_active

        show_sps = ImportApplicationType.objects.get(type=ImportApplicationType.Types.SPS).is_active

        context.update({"show_opt": show_opt, "show_textiles": show_textiles, "show_sps": show_sps})

        return context


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_derogations(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.DEROGATION
    model_class = DerogationsApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_sanctions(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.SANCTION_ADHOC
    model_class = SanctionsAndAdhocApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_oil(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.OIL
    model_class = OpenIndividualLicenceApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_dfl(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.DFL
    model_class = DFLApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_sil(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.SIL
    model_class = SILApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_wood_quota(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.WOOD_QUOTA
    model_class = WoodQuotaApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        form_class=CreateWoodQuotaApplicationForm,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_opt(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.OPT
    model_class = OutwardProcessingTradeApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_textiles(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.TEXTILES
    model_class = TextilesApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_sps(request: AuthenticatedHttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.SPS
    model_class = PriorSurveillanceApplication

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
    )


def _create_application(
    request: AuthenticatedHttpRequest,
    import_application_type: Union[ImportApplicationType.Types, ImportApplicationType.SubTypes],
    model_class: Type[ImportApplication],
    form_class: Type[CreateImportApplicationForm] = None,
) -> HttpResponse:
    """Helper function to create one of several types of importer application.

    :param request: Django request
    :param import_application_type: ImportApplicationType type or sub_type
    :param model_class: ImportApplication class
    :param form_class: Optional form class that defines extra logic
    :return:
    """

    application_type: ImportApplicationType = ImportApplicationType.objects.get(
        Q(type=import_application_type) | Q(sub_type=import_application_type)
    )

    if not application_type.is_active:
        raise ValueError(
            f"Import application of type {application_type.type} ({application_type.sub_type}) is not active"
        )

    if form_class is None:
        form_class = CreateImportApplicationForm

    if request.POST:
        form = form_class(request.POST, user=request.user)

        if form.is_valid():
            application = model_class()
            application.importer = form.cleaned_data["importer"]
            application.importer_office = form.cleaned_data["importer_office"]
            application.process_type = model_class.PROCESS_TYPE
            application.created_by = request.user
            application.last_updated_by = request.user
            application.submitted_by = request.user
            application.application_type = application_type
            application.issue_paper_licence_only = _get_paper_licence_only(application_type)

            with transaction.atomic():
                application.save()
                Task.objects.create(process=application, task_type="prepare", owner=request.user)

            return redirect(
                reverse(application.get_edit_view_name(), kwargs={"application_pk": application.pk})
            )
    else:
        form = form_class(user=request.user)

    show_opt = ImportApplicationType.objects.get(type=ImportApplicationType.Types.OPT).is_active

    show_textiles = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.TEXTILES
    ).is_active

    show_sps = ImportApplicationType.objects.get(type=ImportApplicationType.Types.SPS).is_active

    context = {
        "form": form,
        "import_application_type": application_type,
        "application_title": ImportApplicationType.ProcessTypes(model_class.PROCESS_TYPE).label,
        "show_opt": show_opt,
        "show_textiles": show_textiles,
        "show_sps": show_sps,
    }

    return render(request, "web/domains/case/import/create.html", context)


def _get_paper_licence_only(app_t: ImportApplicationType) -> Optional[bool]:
    """Get initial value for `issue_paper_licence_only` field.

    Some application types have a fixed value, others can choose it in the response
    preparation screen.
    """

    # For when it is hardcoded True
    if app_t.paper_licence_flag and not app_t.electronic_licence_flag:
        return True

    # For when it is hardcoded False
    if app_t.electronic_licence_flag and not app_t.paper_licence_flag:
        return False

    # Default to None so the user can pick it later
    return None


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_cover_letter(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        if request.POST:
            form = CoverLetterForm(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = CoverLetterForm(instance=application)

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Cover Letter Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-cover-letter.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_licence(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application_type: ImportApplicationType = application.application_type

        task = application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        if application.process_type == OutwardProcessingTradeApplication.PROCESS_TYPE:
            form_class = OPTLicenceForm
            application = application.outwardprocessingtradeapplication

        elif application_type.paper_licence_flag and application_type.electronic_licence_flag:
            form_class = LicenceDateAndPaperLicenceForm

        else:
            form_class = LicenceDateForm

        if request.POST:
            form = form_class(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = form_class(instance=application)

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Licence Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-licence.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_endorsement(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    return _add_endorsement(request, application_pk, EndorsementChoiceImportApplicationForm)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_custom_endorsement(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    return _add_endorsement(request, application_pk, EndorsementImportApplicationForm)


def _add_endorsement(
    request: AuthenticatedHttpRequest, application_pk: int, Form: Type[django_forms.ModelForm]
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        if request.POST:
            form = Form(request.POST)

            if form.is_valid():
                endorsement = form.save(commit=False)
                endorsement.import_application = application
                endorsement.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = Form()

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Endorsement Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/add-endorsement.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_endorsement(
    request: AuthenticatedHttpRequest, *, application_pk: int, endorsement_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        endorsement = get_object_or_404(application.endorsements, pk=endorsement_pk)
        task = application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        if request.POST:
            form = EndorsementImportApplicationForm(request.POST, instance=endorsement)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = EndorsementImportApplicationForm(instance=endorsement)

        context = {
            "case_type": "import",
            "process": application,
            "task": task,
            "page_title": "Endorsement Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-endorsement.html",
            context=context,
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def delete_endorsement(
    request: AuthenticatedHttpRequest, *, application_pk: int, endorsement_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        endorsement = get_object_or_404(application.endorsements, pk=endorsement_pk)
        application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        endorsement.delete()

        return redirect(
            reverse(
                "case:prepare-response",
                kwargs={"application_pk": application_pk, "case_type": "import"},
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_GET
def preview_cover_letter(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        context = {
            "process": application,
            "task": task,
            "page_title": "Cover Letter Preview",
            "issue_date": application.licence_issue_date.strftime("%d %B %Y"),
            "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        }

        html_string = render_to_string(
            request=request,
            template_name="web/domains/case/import/manage/preview-cover-letter.html",
            context=context,
        )

        html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = "filename=CoverLetter.pdf"

        return response


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_GET
def preview_licence(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        context = {
            "process": application,
            "task": task,
            "page_title": "Licence Preview",
            "issue_date": application.licence_issue_date.strftime("%d %B %Y"),
        }

        # TODO: preview-licence.html contents are hard-coded and seem to be for
        # a specific type of firearms application. needs to be generalized for
        # other application types.
        html_string = render_to_string(
            request=request,
            template_name="web/domains/case/import/manage/preview-licence.html",
            context=context,
        )

        html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = "filename=Licence.pdf"
        return response


# TODO: This can be replaced by the following:
# icms/web/domains/case/views.py -> def view_application_file
def view_file(request, application, related_file_model, file_pk):
    has_perm_importer = request.user.has_perm("web.importer_access")
    has_perm_reference_data = request.user.has_perm("web.reference_data_access")

    if not has_perm_importer and not has_perm_reference_data:
        raise PermissionDenied

    # first check is for case managers (who are not marked as contacts of
    # importers), second is for people submitting applications
    if not has_perm_reference_data and not request.user.has_perm(
        "web.is_contact_of_importer", application.importer
    ):
        raise PermissionDenied

    document = related_file_model.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response
