from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from web.types import AuthenticatedHttpRequest
from web.utils.companieshouse import api_get_companies
from web.utils.postcode import api_postcode_lookup


@login_required
@require_POST
def postcode_lookup(request: AuthenticatedHttpRequest) -> JsonResponse:
    postcode = request.POST["postcode"]

    return JsonResponse(api_postcode_lookup(postcode), safe=False)


@login_required
@require_POST
def company_lookup(request: AuthenticatedHttpRequest) -> JsonResponse:
    query = request.POST["query"]

    companies = api_get_companies(query)

    return JsonResponse(companies, safe=False)
