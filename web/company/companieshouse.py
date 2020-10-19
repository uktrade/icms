import base64

import structlog as logging
from django.conf import settings

import requests


logger = logging.getLogger(__name__)


URL = "https://api.companieshouse.gov.uk/search/companies?q={query}&items_per_page=20"
URL_COMPANY = "https://api.companieshouse.gov.uk/company/{company_number}"
TOKEN = base64.b64encode(bytes(settings.COMPANIES_HOUSE_TOKEN, "utf-8")).decode("utf-8")


class CompaniesHouseException(Exception):
    pass


def api_get_companies(query_string):
    headers = {"Authorization": f"Basic {TOKEN}"}
    response = requests.get(URL.format(query=query_string), headers=headers)
    if response.status_code != 200:
        logger.error(f"Companies house responded with {response.status_code} - {response.text}")
        raise CompaniesHouseException("Invalid response from companies house")
    return response.json()


def api_get_company(company_number):
    headers = {"Authorization": f"Basic {TOKEN}"}
    response = requests.get(URL_COMPANY.format(company_number=company_number), headers=headers)
    if response.status_code != 200:
        logger.error(f"Companies house responded with {response.status_code} - {response.text}")
        raise CompaniesHouseException("Invalid response from companies house")
    if not response.json():
        raise CompaniesHouseException(f"No company found for company number '{company_number}'")
    return response.json()
