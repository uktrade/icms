import datetime as dt
from typing import Any

import django.forms as django_forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView
from django_ratelimit import UNSAFE
from django_ratelimit.decorators import ratelimit
from guardian.shortcuts import get_objects_for_user

from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.chief import types as chief_types
from web.domains.chief import utils as chief_utils
from web.flow.models import ProcessTypes
from web.models import (
    Country,
    DFLApplication,
    ICMSHMRCChiefRequest,
    ImportApplication,
    ImportApplicationLicence,
    ImportApplicationType,
    Importer,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    Task,
    WoodQuotaApplication,
)
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest

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


def _get_active_application_types() -> dict[str, QuerySet]:
    application_types = ImportApplicationType.objects.filter(is_active=True)
    return {
        "fa_application_types": application_types.filter(type=ImportApplicationType.Types.FIREARMS),
        "other_application_types": application_types.exclude(
            type=ImportApplicationType.Types.FIREARMS
        ),
    }


class ImportApplicationChoiceView(PermissionRequiredMixin, TemplateView):
    template_name = "web/domains/case/import/choose.html"
    permission_required = Perms.sys.importer_access

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(**_get_active_application_types())
        return context


@login_required
@permission_required(Perms.sys.importer_access, raise_exception=True)
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def create_sanctions(request: AuthenticatedHttpRequest) -> HttpResponse:
    return _create_application(
        request,
        application_type=ImportApplicationType.Types.SANCTION_ADHOC,
        model_class=SanctionsAndAdhocApplication,
    )


@login_required
@permission_required(Perms.sys.importer_access, raise_exception=True)
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def create_firearms_oil(request: AuthenticatedHttpRequest) -> HttpResponse:
    return _create_application(
        request,
        application_type=ImportApplicationType.Types.FIREARMS,
        application_subtype=ImportApplicationType.SubTypes.OIL,
        model_class=OpenIndividualLicenceApplication,
    )


@login_required
@permission_required(Perms.sys.importer_access, raise_exception=True)
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def create_firearms_dfl(request: AuthenticatedHttpRequest) -> HttpResponse:
    return _create_application(
        request,
        application_type=ImportApplicationType.Types.FIREARMS,
        application_subtype=ImportApplicationType.SubTypes.DFL,
        model_class=DFLApplication,
    )


@login_required
@permission_required(Perms.sys.importer_access, raise_exception=True)
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def create_firearms_sil(request: AuthenticatedHttpRequest) -> HttpResponse:
    return _create_application(
        request,
        application_type=ImportApplicationType.Types.FIREARMS,
        application_subtype=ImportApplicationType.SubTypes.SIL,
        model_class=SILApplication,
    )


@login_required
@permission_required(Perms.sys.importer_access, raise_exception=True)
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def create_wood_quota(request: AuthenticatedHttpRequest) -> HttpResponse:
    return _create_application(
        request,
        application_type=ImportApplicationType.Types.WOOD_QUOTA,
        model_class=WoodQuotaApplication,
        form_class=CreateWoodQuotaApplicationForm,
    )


@login_required
@permission_required(Perms.sys.importer_access, raise_exception=True)
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def create_sps(request: AuthenticatedHttpRequest) -> HttpResponse:
    return _create_application(
        request,
        application_type=ImportApplicationType.Types.SPS,
        model_class=PriorSurveillanceApplication,
    )


def _create_application(
    request: AuthenticatedHttpRequest,
    *,
    application_type: ImportApplicationType.Types,
    application_subtype: ImportApplicationType.SubTypes | None = None,
    model_class: type[ImportApplication],
    form_class: type[CreateImportApplicationForm] | None = None,
) -> HttpResponse:
    """Helper function to create one of several types of importer application.

    :param request: Django request
    :param import_application_type: ImportApplicationType type or sub_type
    :param model_class: ImportApplication class
    :param form_class: Optional form class that defines extra logic
    :return:
    """

    qs = ImportApplicationType.objects.filter(type=application_type)

    if application_subtype:
        qs = qs.filter(sub_type=application_subtype)

    at: ImportApplicationType = qs.get()

    if not at.is_active:
        raise ValueError(f"Import application of type {at.type} ({at.sub_type}) is not active")

    if form_class is None:
        form_class = CreateImportApplicationForm

    if request.method == "POST":
        form = form_class(request.POST, user=request.user)

        if form.is_valid():
            application = model_class()
            application.importer = form.cleaned_data["importer"]
            application.importer_office = form.cleaned_data["importer_office"]
            application.agent = form.cleaned_data["agent"]
            application.agent_office = form.cleaned_data["agent_office"]
            application.process_type = model_class.PROCESS_TYPE
            application.created_by = request.user
            application.last_updated_by = request.user
            application.application_type = at

            with transaction.atomic():
                application.save()
                Task.objects.create(
                    process=application, task_type=Task.TaskType.PREPARE, owner=request.user
                )

                # Add a draft licence when creating an application
                # Ensures we never have to check for None
                document_pack.pack_draft_create(application)

            return redirect(
                reverse(application.get_edit_view_name(), kwargs={"application_pk": application.pk})
            )
    else:
        form = form_class(user=request.user)

    importers_with_agents = get_objects_for_user(
        request.user, [Perms.obj.importer.is_agent], Importer
    ).values_list("pk", flat=True)

    context = {
        "form": form,
        "import_application_type": at,
        "application_title": ProcessTypes(model_class.PROCESS_TYPE).label,
        "importers_with_agents": list(importers_with_agents),
        **_get_active_application_types(),
    }

    return render(request, "web/domains/case/import/create.html", context)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_cover_letter(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        if request.method == "POST":
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
            "page_title": "Cover Letter Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-cover-letter.html",
            context=context,
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_licence(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application_type: ImportApplicationType = application.application_type

        case_progress.application_in_processing(application)

        form_kwargs: dict[str, Any] = {"instance": document_pack.pack_draft_get(application)}

        if application.process_type == OutwardProcessingTradeApplication.PROCESS_TYPE:
            form_class = OPTLicenceForm
            application = application.get_specific_model()
            # Load the data from the opt record
            form_kwargs["initial"] = {"reimport_period": application.reimport_period}

        elif application_type.paper_licence_flag and application_type.electronic_licence_flag:
            form_class = LicenceDateAndPaperLicenceForm

        else:
            form_class = LicenceDateForm

        if request.method == "POST":
            form = form_class(request.POST, **form_kwargs)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = form_class(**form_kwargs)

        context = {
            "case_type": "import",
            "process": application,
            "page_title": "Licence Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-licence.html",
            context=context,
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def add_endorsement(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    return _add_endorsement(request, application_pk, EndorsementChoiceImportApplicationForm)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def add_custom_endorsement(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    return _add_endorsement(request, application_pk, EndorsementImportApplicationForm)


def _add_endorsement(
    request: AuthenticatedHttpRequest, application_pk: int, Form: type[django_forms.ModelForm]
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        if request.method == "POST":
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
            "page_title": "Endorsement Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/add-endorsement.html",
            context=context,
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_endorsement(
    request: AuthenticatedHttpRequest, *, application_pk: int, endorsement_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        endorsement = get_object_or_404(application.endorsements, pk=endorsement_pk)

        case_progress.application_in_processing(application)

        if request.method == "POST":
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
            "page_title": "Endorsement Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-endorsement.html",
            context=context,
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def delete_endorsement(
    request: AuthenticatedHttpRequest, *, application_pk: int, endorsement_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        endorsement = get_object_or_404(application.endorsements, pk=endorsement_pk)
        case_progress.application_in_processing(application)
        endorsement.delete()

        return redirect(
            reverse(
                "case:prepare-response",
                kwargs={"application_pk": application_pk, "case_type": "import"},
            )
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def bypass_chief(
    request: AuthenticatedHttpRequest, *, application_pk: int, chief_status: str
) -> HttpResponse:
    if settings.SEND_LICENCE_TO_CHIEF or not settings.ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD:
        raise PermissionDenied

    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        # Get the latest fake ICMSHMRCChiefRequest record
        chief_req = ICMSHMRCChiefRequest.objects.latest("pk")

        if chief_status == "success":
            chief_utils.chief_licence_reply_approve_licence(application)
            chief_utils.complete_chief_request(chief_req)

        elif chief_status == "failure":
            chief_utils.chief_licence_reply_reject_licence(application)
            errors = [chief_types.ResponseError(error_code=999, error_msg="Test Failure")]

            chief_utils.fail_chief_request(chief_req, errors)

        messages.success(
            request,
            f"CHIEF: faked {chief_status} for application {application.get_reference()}.",
        )

        return redirect(reverse("workbasket"))


class IMICaseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Shows a list of cases that need information sending to the EU.

    The logic in V1 is different to the logic added to v2 and is documented in the following ticket:
    https://uktrade.atlassian.net/browse/ICMSLST-1177

    In case that ticket gets deleted here is a summary of logic provided by ILB:

    IMI is not relevant to the following:
        - FA-OIL:
            because they cover types of firearms that we do not need to give notification to the
            EU Commission. Essentially those that are not section 5.
        - FA-DFL:
            because they are not live firearms.

    IMI conditions:
        BT postcode only:
            IMI is not relevant to GB because of EU exit. NI is relevant because of the Windsor
            Framework.
        SIL:
            this is the only current firearms licence type which will be used in respect of the
            firearms that are impacted.
        EU member state country of consignment:
            it is only relevant to shipments from EU to NI.
            This ensures compliance with the requirements of an EU firearms directive which
            continues to apply to NI .

    It will likely have been originally set up to cover all UK SIL but this will have changed
    following EU Exit and the impact of the Windsor Framework and has not been picked up as a
    necessary system change.
    """

    http_method_names = ["get"]
    permission_required = Perms.page.view_imi
    template_name = "web/domains/case/import/imi/list.html"
    context_object_name = "imi_list"
    extra_context = {"page_title": "IMI Applications"}

    def get_queryset(self) -> "QuerySet[ImportApplication]":
        """Return all applications that have been acknowledged."""
        eu_countries = Country.util.get_eu_countries()
        qs = ImportApplication.objects.filter(
            application_type__type=ImportApplicationType.Types.FIREARMS,
            application_type__sub_type=ImportApplicationType.SubTypes.SIL,
            status=ImpExpStatus.COMPLETED,
            decision=ImportApplication.APPROVE,
            importer_office__postcode__istartswith="BT",
            consignment_country__in=eu_countries,
            imi_submitted_by__isnull=True,
            legacy_case_flag=False,
            # Extra date filter to remove old records noticed in v2 after data migration
            submit_datetime__gte=dt.datetime(2024, 1, 1, 0, 0, tzinfo=dt.UTC),
        ).order_by("-submit_datetime")

        return qs


class IMICaseDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    template_name = "web/domains/case/manage/imi-case-detail.html"
    permission_required = Perms.page.view_imi
    pk_url_kwarg = "application_pk"
    context_object_name = "process"
    queryset = ImportApplication.objects.select_related(
        "importer", "importer_office", "case_owner", "application_type", "contact"
    )

    def get_context_data(self, **kwargs):
        licence: ImportApplicationLicence = document_pack.pack_active_get(self.object)
        licence_doc = document_pack.doc_ref_licence_get_optional(licence)

        if licence_doc and licence_doc.document:
            reference = licence_doc.reference
            reference_link = reverse(
                "case:view-case-document",
                kwargs={
                    "application_pk": self.object.id,
                    "case_type": "import",
                    "object_pk": licence.pk,
                    "casedocumentreference_pk": licence_doc.pk,
                },
            )
        else:
            reference = ""
            reference_link = "#"

        context = {
            "page_title": f"Case {self.object.get_reference()}",
            "case_type": "import",
            "show_imi_detail": True,
            "contacts": self.object.importcontact_set.all(),
            "licence": licence,
            "licence_reference": reference,
            "licence_reference_link": reference_link,
            # Set to true as all IMI applications are complete.
            "readonly_view": True,
        }

        return super().get_context_data(**kwargs) | context


@require_POST
@permission_required(Perms.page.view_imi, raise_exception=True)
@login_required
def imi_confirm_provided(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    """Indicates the relevant details have been sent to IMI."""

    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        application.imi_submitted_by = request.user
        application.imi_submit_datetime = timezone.now()
        application.save()

    return redirect(reverse("import:imi-case-detail", kwargs={"application_pk": application_pk}))
