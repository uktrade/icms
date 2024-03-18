from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from web.errors import APIError, CompanyNotFound
from web.types import AuthenticatedHttpRequest
from web.utils.companieshouse import api_get_companies, api_get_company
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


@login_required
@require_POST
def company_number_lookup(request: AuthenticatedHttpRequest) -> JsonResponse:
    """Fetches a single company from CompaniesHouse from its company number"""

    if company_number := request.POST.get("company_number"):
        try:
            company_data = api_get_company(company_number)
            return JsonResponse(
                company_data,
                safe=False,
            )
        except CompanyNotFound:
            return JsonResponse({"error_msg": "Company not found"}, status=404)
        except APIError as e:
            capture_exception()
            return JsonResponse({"error_msg": e.error_msg}, status=e.status_code)
        except Exception:
            capture_exception()
            return JsonResponse({"error_msg": "Unable to lookup company"}, status=500)

    else:
        return JsonResponse({"error_msg": "No company_number provided in POST request"}, status=400)
