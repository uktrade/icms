from typing import TYPE_CHECKING, Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

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

from .mixins import ApplicationUpdateView

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.domains.user.models import User
    from web.flow.models import Process

SearchForm = Union[
    ExportSearchAdvancedForm, ExportSearchForm, ImportSearchAdvancedForm, ImportSearchForm
]
SearchFormT = Type[SearchForm]


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def search_cases(
    request: AuthenticatedHttpRequest, *, case_type: str, mode: str = "normal"
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

    if request.POST:
        form = form_class(request.POST)

        if form.is_valid():
            show_search_results = True
            terms = _get_search_terms_from_form(case_type, form)
            results = search_applications(terms, request.user)

            total_rows = results.total_rows
            search_records = results.records

        show_application_sub_type = (
            form.cleaned_data.get("application_type") == ImportApplicationType.Types.FIREARMS
        )

    else:
        form = form_class(initial={"reassignment": False})

    context = {
        "form": form,
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
class ReopenApplicationView(ApplicationUpdateView):
    permission_required = ["web.ilb_admin"]

    current_status = [ApplicationBase.Statuses.STOPPED, ApplicationBase.Statuses.WITHDRAWN]
    current_task = None

    next_status = ApplicationBase.Statuses.SUBMITTED
    next_task_type = Task.TaskType.PROCESS

    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> HttpResponse:
        """Reopen the application."""

        super().post(request, *args, **kwargs)

        self.update_application_status(commit=False)
        self.application.case_owner = None
        self.application.save()

        self.update_application_tasks()

        return HttpResponse(status=204)


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
