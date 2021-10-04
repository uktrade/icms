from typing import Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from web.domains.case._import.models import ImportApplicationType
from web.domains.case.forms_search import (
    ExportSearchAdvancedForm,
    ExportSearchForm,
    ImportSearchAdvancedForm,
    ImportSearchForm,
)
from web.types import AuthenticatedHttpRequest
from web.utils.search import (
    SearchTerms,
    get_search_results_spreadsheet,
    search_applications,
)

SearchForm = Union[
    ExportSearchAdvancedForm, ExportSearchForm, ImportSearchAdvancedForm, ImportSearchForm
]
SearchFormT = Type[SearchForm]


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
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
            results = search_applications(terms)

            total_rows = results.total_rows
            search_records = results.records

        show_application_sub_type = (
            form.cleaned_data.get("application_type") == ImportApplicationType.Types.FIREARMS
        )

    else:
        form = form_class()

    context = {
        "form": form,
        "case_type": case_type,
        "page_title": f"Search {app_type} Applications",
        "advanced_search": mode == "advanced",
        "show_search_results": show_search_results,
        "show_application_sub_type": show_application_sub_type,
        "total_rows": total_rows,
        "search_records": search_records,
    }

    return render(
        request=request,
        template_name="web/domains/case/search/search.html",
        context=context,
    )


@require_POST
@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def download_spreadsheet(request: AuthenticatedHttpRequest, *, case_type: str) -> HttpResponse:
    """Generates and returns a spreadsheet using same form data as the search form."""

    # TODO: Revisit when doing ICMSLST-1153
    # I think the form class just needs to use the AdvancedSearchForm's
    form_class: SearchFormT = ImportSearchForm if case_type == "import" else ExportSearchForm
    form = form_class(request.POST)

    if not form.is_valid():
        return HttpResponse(status=400)

    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response = HttpResponse(content_type=mime_type)

    terms = _get_search_terms_from_form(case_type, form)
    results = search_applications(terms)
    search_spreadsheet = get_search_results_spreadsheet(case_type, results)
    response.write(search_spreadsheet)

    response["Content-Disposition"] = f"attachment; filename={case_type}_application_download.xlsx"

    return response


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
        response_decision=cd.get("decision"),
        submitted_date_start=cd.get("submitted_from"),
        submitted_date_end=cd.get("submitted_to"),
        reassignment_search=cd.get("reassignment"),
        # ---- Import application fields ----
        # icms_legacy_cases = str = None
        app_sub_type=cd.get("application_sub_type"),
        importer_agent_name=cd.get("importer_or_agent"),
        licence_date_start=cd.get("licence_from"),
        licence_date_end=cd.get("licence_to"),
        issue_date_start=cd.get("issue_from"),
        issue_date_end=cd.get("issue_to"),
        # ---- Export application fields ----
        exporter_agent_name=cd.get("exporter_or_agent"),
        closed_date_start=cd.get("closed_from"),
        closed_date_end=cd.get("closed_to"),
        certificate_country=cd.get("cert_country"),
        manufacture_country=cd.get("manufacture_country"),
        pending_firs=cd.get("pending_firs"),
        pending_update_reqs=cd.get("pending_update_reqs"),
    )
