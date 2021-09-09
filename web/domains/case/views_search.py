from typing import Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import render

from web.domains.case._import.models import ImportApplicationType
from web.types import AuthenticatedHttpRequest
from web.utils.search import SearchTerms, search_applications

from .forms_search import ExportSearchForm, ImportSearchForm

SearchForm = Union[ImportSearchForm, ExportSearchForm]
SearchFormT = Type[SearchForm]


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def search_cases(request: AuthenticatedHttpRequest, *, case_type: str) -> HttpResponse:
    form_class: SearchFormT = ImportSearchForm if case_type == "import" else ExportSearchForm
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


def _get_search_terms_from_form(case_type: str, form: SearchForm) -> SearchTerms:
    """Load the SearchTerms from the form data."""

    cd = form.cleaned_data

    return SearchTerms(
        case_type=case_type,
        case_ref=cd.get("case_ref"),
        licence_ref=cd.get("licence_ref"),
        app_type=cd.get("application_type"),
        app_sub_type=cd.get("application_sub_type"),
        case_status=cd.get("status"),
        response_decision=cd.get("decision"),
        importer_agent_name=cd.get("importer_or_agent"),
        submitted_date_start=cd.get("submitted_from"),
        submitted_date_end=cd.get("submitted_to"),
        licence_date_start=cd.get("licence_from"),
        licence_date_end=cd.get("licence_to"),
        issue_date_start=cd.get("issue_from"),
        issue_date_end=cd.get("issue_to"),
        reassignment_search=cd.get("reassignment"),
        # TODO: add all the export search fields
    )
