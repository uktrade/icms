import base64
import logging
from typing import Any

import requests
from django.conf import settings

from web.errors import APIError, CompanyNotFound

logger = logging.getLogger(__name__)


def api_get_companies(query_string: str) -> dict[str, Any]:
    url = _get_companies_url(query_string)
    response = requests.get(url, headers=_get_auth_header())

    if response.status_code != 200:
        error_msg = "Unable to lookup company"
        logger.error("Companies house responded with %s - %s", response.status_code, response.text)

        raise APIError(error_msg, "", response.status_code)

    return response.json()


def api_get_company(company_number: str) -> dict[str, Any] | None:
    url = _get_company_profile_url(company_number)
    response = requests.get(url, headers=_get_auth_header())

    if response.status_code != 200:
        if response.status_code == 404:
            raise CompanyNotFound()
        else:
            error_msg = "Unable to lookup company"
            logger.error(
                "Companies house responded with %s - %s", response.status_code, response.text
            )

        raise APIError(error_msg, "", response.status_code)

    return response.json()


def _get_company_profile_url(company_number: str) -> str:
    """https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/company-profile/company-profile"""
    return f"{settings.COMPANIES_HOUSE_DOMAIN}company/{company_number}"


def _get_companies_url(query: str) -> str:
    """https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/search/search-companies"""
    return f"{settings.COMPANIES_HOUSE_DOMAIN}search/companies?q={query}&items_per_page=20"


def _get_auth_header() -> dict[str, str]:
    token = base64.b64encode(bytes(settings.COMPANIES_HOUSE_TOKEN, "utf-8")).decode(  # /PS-IGNORE
        "utf-8"
    )

    return {"Authorization": f"Basic {token}"}
