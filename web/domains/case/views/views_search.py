from typing import TYPE_CHECKING, Type, Union
from urllib import parse

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import FormView, View

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.case.export.models import ExportApplication
from web.domains.case.forms_search import (
    ExportSearchAdvancedForm,
    ExportSearchForm,
    ImportSearchAdvancedForm,
    ImportSearchForm,
    ReassignmentUserForm,
)
from web.domains.case.models import ApplicationBase
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.search import (
    SearchTerms,
    get_search_results_spreadsheet,
    search_applications,
)

from ..forms import RequestVariationForm
from ..models import VariationRequest
from .mixins import ApplicationTaskMixin

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.domains.user.models import User
    from web.flow.models import Process

SearchForm = Union[
    ExportSearchAdvancedForm, ExportSearchForm, ImportSearchAdvancedForm, ImportSearchForm
]
SearchFormT = Type[SearchForm]


@require_GET
@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def search_cases(
    request: AuthenticatedHttpRequest, *, case_type: str, mode: str = "standard", get_results=False
) -> HttpResponse:

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
        "reassignment_search": form["reassignment"].value(),
    }

    return render(
        request=request,
        template_name="web/domains/case/search/search.html",
        context=context,
    )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def reassign_case_owner(request: AuthenticatedHttpRequest, *, case_type: str) -> HttpResponse:
    """Reassign Applications to the chosen ILB admin."""

    with transaction.atomic():
        form = ReassignmentUserForm(request.POST)

        if form.is_valid():
            new_case_owner: "User" = form.cleaned_data["assign_to"]
            applications: "QuerySet[Process]" = form.cleaned_data["applications"]

            if case_type == "import":
                apps = ImportApplication.objects.select_for_update().filter(pk__in=applications)
            else:
                apps = ExportApplication.objects.select_for_update().filter(pk__in=applications)

            apps.update(case_owner=new_case_owner)
        else:
            return HttpResponse(status=400)

    return HttpResponse(status=204)


@require_POST
@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def download_spreadsheet(request: AuthenticatedHttpRequest, *, case_type: str) -> HttpResponse:
    """Generates and returns a spreadsheet using same form data as the search form."""

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
    permission_required = ["web.ilb_admin"]

    current_status = [ApplicationBase.Statuses.STOPPED, ApplicationBase.Statuses.WITHDRAWN]
    current_task = None

    next_status = ApplicationBase.Statuses.SUBMITTED
    next_task_type = Task.TaskType.PROCESS

    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        """Reopen the application."""

        self.set_application_and_task()
        self.update_application_status(commit=False)
        self.application.case_owner = None
        self.application.save()

        self.update_application_tasks()

        return HttpResponse(status=204)


@method_decorator(transaction.atomic, name="post")
class RequestVariationUpdateView(
    ApplicationTaskMixin, PermissionRequiredMixin, LoginRequiredMixin, FormView
):
    # ICMSLST-1240 Need to revisit permissions when they become more clear
    # PermissionRequiredMixin config
    permission_required = ["web.ilb_admin"]

    # ApplicationTaskMixin Config
    current_status = [ApplicationBase.Statuses.COMPLETED]
    current_task = None
    next_status = ApplicationBase.Statuses.VARIATION_REQUESTED
    next_task_type = Task.TaskType.PROCESS

    # FormView config
    form_class = RequestVariationForm
    template_name = "web/domains/case/request-variation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context | {"search_results_url": self.get_success_url()}

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""

        variation_request: VariationRequest = form.save(commit=False)

        # Refactor to TextChoice
        variation_request.status = VariationRequest.DRAFT
        variation_request.requested_by = self.request.user

        self.application.variation_requests.add(variation_request)
        self.update_application_status()

        return super().form_valid(form)

    def get_success_url(self):
        """Upon submitting a valid variation request return to the search screen."""

        if self.request.GET.get("return_url", None):
            return self._get_return_url()

        # Default to search with variation requested
        if self.application.is_import_application():
            case_type = "import"
        else:
            case_type = "export"

        search_url = reverse(
            "case:search-results", kwargs={"case_type": case_type, "mode": "standard"}
        )
        query_params = {"case_status": self.application.Statuses.VARIATION_REQUESTED}

        return "".join((search_url, "?", parse.urlencode(query_params)))

    def _get_return_url(self):
        """Check for a return_url query param and rebuild the search request."""

        url = self.request.GET.get("return_url", None)
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


def _get_search_terms_from_form(case_type: str, form: SearchForm) -> SearchTerms:
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
        under_appeal=cd.get("under_appeal"),
        licence_date_start=cd.get("licence_from"),
        licence_date_end=cd.get("licence_to"),
        issue_date_start=cd.get("issue_from"),
        issue_date_end=cd.get("issue_to"),
        # ---- Export application fields ----
        exporter_agent_name=cd.get("exporter_or_agent"),
        closed_date_start=cd.get("closed_from"),
        closed_date_end=cd.get("closed_to"),
        certificate_country=cd.get("certificate_country"),
        manufacture_country=cd.get("manufacture_country"),
    )
