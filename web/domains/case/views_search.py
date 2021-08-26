from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import render

from web.types import AuthenticatedHttpRequest

from .forms_search import ExportSearchForm, ImportSearchForm


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def search_cases(request: AuthenticatedHttpRequest, *, case_type: str) -> HttpResponse:
    if case_type == "import":
        form_class = ImportSearchForm
    else:
        form_class = ExportSearchForm

    if request.POST:
        form = form_class(request.POST)

        if form.is_valid():
            # TODO: ICMSLST-1033 implement actual search logic
            pass
    else:
        form = form_class()

    context = {
        "form": form,
        "case_type": case_type,
        "page_title": "Search %s Applications"
        % ("Import" if case_type == "import" else "Certificate",),
    }

    return render(
        request=request,
        template_name="web/domains/case/search/search.html",
        context=context,
    )
