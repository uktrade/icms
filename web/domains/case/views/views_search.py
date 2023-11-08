from typing import Any, Literal, Union
from urllib import parse

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet, Window
from django.db.models.functions import RowNumber
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import FormView, View

from web.domains.case.forms import (
    RevokeApplicationForm,
    VariationRequestExportAppForm,
    VariationRequestForm,
)
from web.domains.case.forms_search import (
    ExportSearchAdvancedForm,
    ExportSearchForm,
    ImportSearchAdvancedForm,
    ImportSearchForm,
    ReassignmentUserForm,
)
from web.domains.case.services import case_progress, document_pack, reference
from web.domains.case.shared import ImpExpStatus
from web.domains.chief import client
from web.mail.emails import (
    send_application_reopened_email,
    send_certificate_revoked_email,
    send_licence_revoked_email,
)
from web.models import (
    ExportApplication,
    ImportApplication,
    ImportApplicationType,
    Process,
    Task,
    User,
    VariationRequest,
)
from web.permissions import AppChecker, Perms, can_user_view_search_cases
from web.types import AuthenticatedHttpRequest
from web.utils.search import (
    SearchTerms,
    get_search_results_spreadsheet,
    search_applications,
)

from .mixins import ApplicationTaskMixin

SearchForm = Union[
    ExportSearchAdvancedForm, ExportSearchForm, ImportSearchAdvancedForm, ImportSearchForm
]
SearchFormT = type[SearchForm]


@require_GET
@login_required
def search_cases(
    request: AuthenticatedHttpRequest,
    *,
    case_type: Literal["import", "export"],
    mode: str = "standard",
    get_results=False,
) -> HttpResponse:
    if not can_user_view_search_cases(request.user, case_type):
        raise PermissionDenied

    if mode == "advanced":
        form_class: SearchFormT = (
            ImportSearchAdvancedForm if case_type == "import" else ExportSearchAdvancedForm
        )
    else:
        form_class = ImportSearchForm if case_type == "import" else ExportSearchForm

    app_type = "Import" if case_type == "import" else "Certificate"
    show_search_results = False
    total_rows = 0
    search_records = []
    show_application_sub_type = False

    form = form_class(request.GET)

    if form.is_valid() and get_results:
        show_search_results = True
        terms = _get_search_terms_from_form(case_type, form)
        results = search_applications(terms, request.user)

        total_rows = results.total_rows
        search_records = results.records

        show_application_sub_type = (
            form.cleaned_data.get("application_type") == ImportApplicationType.Types.FIREARMS
        )

    results_url = reverse("case:search-results", kwargs={"case_type": case_type, "mode": mode})

    reassignment_search_enabled = request.user.has_perm(Perms.sys.ilb_admin)

    context = {
        "form": form,
        "results_url": results_url,
        "reassignment_form": ReassignmentUserForm(),
        "case_type": case_type,
        "page_title": f"Search {app_type} Applications",
        "advanced_search": mode == "advanced",
        "show_search_results": show_search_results,
        "show_application_sub_type": show_application_sub_type,
        "total_rows": total_rows,
        "search_records": search_records,
        "reassignment_search": reassignment_search_enabled and form["reassignment"].value(),
        "reassignment_enabled": reassignment_search_enabled,
    }

    return render(
        request=request,
        template_name="web/domains/case/search/search.html",
        context=context,
    )


@require_POST
@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def reassign_case_owner(request: AuthenticatedHttpRequest, *, case_type: str) -> HttpResponse:
    """Reassign Applications to the chosen ILB admin."""

    with transaction.atomic():
        form = ReassignmentUserForm(request.POST)

        if form.is_valid():
            new_case_owner: User = form.cleaned_data["assign_to"]
            applications: QuerySet[Process] = form.cleaned_data["applications"]

            if case_type == "import":
                apps = ImportApplication.objects.select_for_update().filter(pk__in=applications)
            else:
                apps = ExportApplication.objects.select_for_update().filter(pk__in=applications)

            now = timezone.now()
            apps.update(case_owner=new_case_owner, order_datetime=now, reassign_datetime=now)
        else:
            return HttpResponse(status=400)

    return HttpResponse(status=204)


@require_POST
@login_required
def download_spreadsheet(
    request: AuthenticatedHttpRequest, *, case_type: Literal["import", "export"]
) -> HttpResponse:
    """Generates and returns a spreadsheet using same form data as the search form."""
    if not can_user_view_search_cases(request.user, case_type):
        raise PermissionDenied

    form_class: SearchFormT = (
        ImportSearchAdvancedForm if case_type == "import" else ExportSearchAdvancedForm
    )
    form = form_class(request.POST)

    if not form.is_valid():
        return HttpResponse(status=400)

    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response = HttpResponse(content_type=mime_type)

    terms = _get_search_terms_from_form(case_type, form)
    results = search_applications(terms, request.user)
    search_spreadsheet = get_search_results_spreadsheet(case_type, results)
    response.write(search_spreadsheet)

    response["Content-Disposition"] = f"attachment; filename={case_type}_application_download.xlsx"

    return response


@method_decorator(transaction.atomic, name="post")
class ReopenApplicationView(
    ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, View
):
    permission_required = [Perms.sys.ilb_admin]

    # ApplicationTaskMixin Config
    current_status = [ImpExpStatus.STOPPED, ImpExpStatus.WITHDRAWN]
    current_task_type = None

    next_status = ImpExpStatus.SUBMITTED
    next_task_type = Task.TaskType.PROCESS

    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        """Reopen the application."""
        self.set_application_and_task()
        self.application.case_owner = None
        self.application.is_active = True

        self.application.update_order_datetime()
        self.update_application_status()
        self.update_application_tasks()
        document_pack.pack_draft_create(self.application)

        messages.success(
            request,
            "The case has been reopened, and can be taken ownership of by any case manager.",
        )
        send_application_reopened_email(self.application)

        # The page reload is handled in JS to preserve the search form state.
        # see web/static/web/js/pages/search-common.js
        return HttpResponse(status=204)


class SearchActionFormBase(
    ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, FormView
):
    """Base class for showing a form view that retains the previous search results."""

    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        # Store the search url to create the return link later
        referrer = self.request.META.get("HTTP_REFERER", "")

        if "search/standard" in referrer or "search/advanced" in referrer:
            self.request.session["search_results_url"] = referrer

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "search_results_url": self.get_success_url(),
        }

    def get_success_url(self) -> str:
        """Upon submitting a valid variation request return to the search screen."""
        if self.request.session.get("search_results_url"):
            return self._get_return_url()

        return self._default_return_url()

    def _get_return_url(self) -> str:
        """Check for a search_results_url and rebuild the search request."""

        url = self.request.session.get("search_results_url")
        return_url: parse.ParseResult = parse.urlparse(url)

        is_import = "case/import/" in return_url.path
        is_standard = "search/standard/" in return_url.path

        search_url = reverse(
            "case:search-results",
            kwargs={
                "case_type": "import" if is_import else "export",
                "mode": "standard" if is_standard else "advanced",
            },
        )

        if return_url.query:
            search_url = "".join((search_url, "?", return_url.query))

        return search_url

    def _default_return_url(self):
        raise NotImplementedError("View must define _default_return_url")


class RequestVariationOpenBase(SearchActionFormBase):
    """Base class for opening a variation request for import and export applications."""

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Returns context data for both import and export application variation requests."""

        context = super().get_context_data(**kwargs)

        variation_requests = self.application.variation_requests.order_by(
            "-requested_datetime"
        ).annotate(vr_num=Window(expression=RowNumber()))

        return context | {
            "page_title": f"Application {self.application.get_reference()}",
            "process": self.application,
            "case_type": self.kwargs["case_type"],
            "variation_requests": variation_requests,
        }

    def _default_return_url(self) -> str:
        """Default to search with variation requested"""

        case_type = "import" if self.application.is_import_application() else "export"
        search_url = reverse(
            "case:search-results", kwargs={"case_type": case_type, "mode": "standard"}
        )
        query_params = {"case_status": self.application.Statuses.VARIATION_REQUESTED}

        return "".join((search_url, "?", parse.urlencode(query_params)))

    def clear_application_cleared_by(self) -> None:
        self.application.cleared_by.clear()


@method_decorator(transaction.atomic, name="post")
class RequestVariationUpdateView(RequestVariationOpenBase):
    """View to open a variation request for an import application"""

    permission_required = [Perms.page.view_import_case_search]

    # ApplicationTaskMixin Config
    current_status = [ImpExpStatus.COMPLETED]
    current_task_type = None
    next_status = ImpExpStatus.VARIATION_REQUESTED
    next_task_type = Task.TaskType.PROCESS

    # FormView config
    form_class = VariationRequestForm
    template_name = "web/domains/case/variation-request-add.html"

    def has_object_permission(self) -> bool:
        """Return True if the user has the correct object permissions."""

        return AppChecker(self.request.user, self.application).can_vary()

    def form_valid(self, form: VariationRequestForm) -> HttpResponseRedirect:
        """Store the variation request before redirecting to the success url."""

        variation_request: VariationRequest = form.save(commit=False)
        variation_request.status = VariationRequest.Statuses.OPEN
        variation_request.requested_by = self.request.user
        variation_request.save()

        self.application.variation_requests.add(variation_request)
        self.application.case_owner = None
        self.application.variation_decision = None
        self.application.variation_refuse_reason = None

        self.application.reference = reference.get_variation_request_case_reference(
            self.application
        )
        self.application.update_order_datetime()
        self.update_application_status()
        self.update_application_tasks()
        self.clear_application_cleared_by()

        document_pack.pack_draft_create(self.application, variation_request=True)

        return super().form_valid(form)


@method_decorator(transaction.atomic, name="post")
class RequestVariationOpenRequestView(RequestVariationOpenBase):
    """Admin view to open a variation request for an export application"""

    # PermissionRequiredMixin config
    permission_required = [Perms.sys.ilb_admin]

    # ApplicationTaskMixin Config
    current_status = [ImpExpStatus.COMPLETED]
    current_task_type = None
    next_status = ImpExpStatus.VARIATION_REQUESTED
    next_task_type = Task.TaskType.PROCESS

    # FormView config
    form_class = VariationRequestExportAppForm
    template_name = "web/domains/case/variation-request-add.html"

    def form_valid(self, form: VariationRequestForm) -> HttpResponseRedirect:
        """Store the variation request before redirecting to the success url."""

        variation_request: VariationRequest = form.save(commit=False)
        variation_request.status = VariationRequest.Statuses.OPEN
        variation_request.requested_by = self.request.user
        variation_request.save()

        self.application.variation_requests.add(variation_request)
        self.application.case_owner = None
        self.application.reference = reference.get_variation_request_case_reference(
            self.application
        )

        self.application.update_order_datetime()
        self.update_application_status()
        self.update_application_tasks()
        self.clear_application_cleared_by()

        # Create a new draft licence for this variation
        document_pack.pack_draft_create(self.application, variation_request=True)

        return super().form_valid(form)


@method_decorator(transaction.atomic, name="post")
class RevokeCaseView(SearchActionFormBase):
    """Admin view to revoke an application."""

    # PermissionRequiredMixin config
    permission_required = [Perms.sys.ilb_admin]

    # ApplicationTaskMixin Config
    current_status = [ImpExpStatus.COMPLETED, ImpExpStatus.REVOKED]
    next_status = ImpExpStatus.REVOKED

    # FormView config
    form_class = RevokeApplicationForm
    template_name = "web/domains/case/manage/revoke-licence.html"

    def get_template_names(self):
        if self.application.is_import_application():
            return ["web/domains/case/manage/revoke-licence.html"]
        else:
            return ["web/domains/case/manage/revoke-certificate.html"]

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if self.application.status == ImpExpStatus.COMPLETED:
            context["active_pack"] = document_pack.pack_active_get(self.application)
        else:
            context["active_pack"] = None

        return context | {
            "page_title": f"Application {self.application.get_reference()}",
            "process": self.application,
            "case_type": self.kwargs["case_type"],
            "show_revocation": True,
            # This is a complete application so set readonly_view to True
            "readonly_view": True,
        }

    def get_initial(self) -> dict[str, Any]:
        """Return the initial data to use for forms on this view.

        When an application has already been revoked we load that data.
        """
        initial = super().get_initial()

        if self.application.status == ImpExpStatus.COMPLETED:
            return initial

        # When showing complete revocation load the data from the revoked licence
        licence = document_pack.pack_revoked_get(self.application)

        return initial | {
            "send_email": licence.revoke_email_sent,
            "reason": licence.revoke_reason,
        }

    def get_form_kwargs(self) -> dict[str, Any]:
        """Return the keyword arguments for instantiating the form.

        When an application has already been revoked we disable each form field.
        """
        kwargs = super().get_form_kwargs()

        if self.application.status == ImpExpStatus.REVOKED:
            kwargs["readonly_form"] = True

        return kwargs

    def form_valid(self, form: RevokeApplicationForm) -> HttpResponseRedirect:
        """Revoke the licence before redirecting to the success url."""
        # This view allows both completed and revoked.
        # The POST form submission only allows an application in the completed state.
        case_progress.check_expected_status(self.application, [ImpExpStatus.COMPLETED])
        email_applicants = form.cleaned_data["send_email"]
        reason = form.cleaned_data["reason"]
        is_import = self.application.is_import_application()

        document_pack.pack_active_revoke(self.application, reason, email_applicants)

        self.application.update_order_datetime()
        self.update_application_status()

        if is_import and self.application.application_type.chief_flag:
            client.send_application_to_chief(self.application, self.task, revoke_licence=True)

        if email_applicants:
            if is_import:
                send_licence_revoked_email(self.application)
            else:
                send_certificate_revoked_email(self.application)

        return super().form_valid(form)

    def _default_return_url(self) -> str:
        """Default to search showing this application."""
        case_type = "import" if self.application.is_import_application() else "export"
        search_url = reverse(
            "case:search-results", kwargs={"case_type": case_type, "mode": "standard"}
        )
        query_params = {"case_ref": self.application.reference}

        return "".join((search_url, "?", parse.urlencode(query_params)))


def _get_search_terms_from_form(
    case_type: Literal["import", "export"], form: SearchForm
) -> SearchTerms:
    """Load the SearchTerms from the form data."""

    cd = form.cleaned_data

    return SearchTerms(
        case_type=case_type,
        # ---- Common search fields (Import and Export applications) ----
        app_type=cd.get("application_type"),
        case_status=cd.get("status"),
        case_ref=cd.get("case_ref"),
        licence_ref=cd.get("licence_ref"),
        application_contact=cd.get("application_contact"),
        response_decision=cd.get("decision"),
        submitted_date_start=cd.get("submitted_from"),
        submitted_date_end=cd.get("submitted_to"),
        pending_firs=cd.get("pending_firs"),
        pending_update_reqs=cd.get("pending_update_reqs"),
        reassignment_search=cd.get("reassignment"),
        reassignment_user=cd.get("reassignment_user"),
        # ---- Import application fields ----
        # icms_legacy_cases = str = None
        app_sub_type=cd.get("application_sub_type"),
        applicant_ref=cd.get("applicant_ref"),
        importer_agent_name=cd.get("importer_or_agent"),
        licence_type=cd.get("licence_type"),
        chief_usage_status=cd.get("chief_usage_status"),
        origin_country=cd.get("origin_country"),
        consignment_country=cd.get("consignment_country"),
        shipping_year=cd.get("shipping_year"),
        goods_category=cd.get("goods_category"),
        commodity_code=cd.get("commodity_code"),
        licence_date_start=cd.get("licence_from"),
        licence_date_end=cd.get("licence_to"),
        issue_date_start=cd.get("issue_from"),
        issue_date_end=cd.get("issue_to"),
        # ---- Export application fields ----
        exporter_agent_name=cd.get("exporter_or_agent"),
        certificate_country=cd.get("certificate_country"),
        manufacture_country=cd.get("manufacture_country"),
    )
