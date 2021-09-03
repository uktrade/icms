from typing import Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import render

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
    total_rows = 0
    search_records = []

    if request.POST:
        form = form_class(request.POST)

        if form.is_valid():
            terms = _get_search_terms_from_form(case_type, form)
            results = search_applications(terms)

            total_rows = results.total_rows
            search_records = results.records

    else:
        form = form_class()

    context = {
        "form": form,
        "case_type": case_type,
        "page_title": f"Search {app_type} Applications",
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

    return SearchTerms(
        case_type=case_type,
        case_ref=form.data.get("case_ref", None),
        licence_ref=form.data.get("licence_ref", None),
        app_type=form.data.get("application_type", None),
        # app_sub_type=form.application_type,
        case_status=form.data.get("status", None),
        response_decision=form.data.get("decision", None),
        # importer_agent_name=form.case_ref,
        # submitted_datetime_start=form.case_ref,
        # submitted_datetime_end=form.case_ref,
        # licence_date_start=form.case_ref,
        # licence_date_end=form.case_ref,
        # issue_date_start=form.case_ref,
        # issue_date_end=form.case_ref,
        # reassignment_search=form.case_ref,
    )
