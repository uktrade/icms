from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from web.errors import APIError
from web.types import AuthenticatedHttpRequest
from web.utils.companieshouse import api_get_companies
from web.utils.postcode import api_postcode_to_address_lookup
from web.utils.sentry import capture_exception


@login_required
@require_POST
def postcode_lookup(request: AuthenticatedHttpRequest) -> JsonResponse:
    postcode = request.POST["postcode"]

    try:
        addresses = api_postcode_to_address_lookup(postcode)

        return JsonResponse(addresses, safe=False)

    except APIError as e:
        # don't bother logging sentries when users type in invalid postcodes
        if e.status_code not in (400, 404):
            capture_exception()

        response_data = {"error_msg": e.error_msg}

        if settings.APP_ENV in ("local", "dev"):
            response_data["dev_error_msg"] = e.dev_error_msg

    except Exception:
        capture_exception()

        response_data = {"error_msg": "Unable to lookup postcode"}

    return JsonResponse(response_data, status=400)


@login_required
@require_POST
def company_lookup(request: AuthenticatedHttpRequest) -> JsonResponse:
    query = request.POST["query"]

    companies = api_get_companies(query)

    return JsonResponse(companies, safe=False)
