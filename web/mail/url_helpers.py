from urllib.parse import urljoin

from django.conf import settings
from django.shortcuts import reverse
from django.templatetags.static import static

from web.domains.case.types import ImpOrExp
from web.sites import get_caseworker_site_domain


def get_full_url(url: str) -> str:
    return urljoin(settings.DEFAULT_DOMAIN, url)


def get_validate_digital_signatures_url(full_url: bool = False) -> str:
    url = static("web/docs/ValidateDigSigs.pdf")
    if full_url:
        domain = get_caseworker_site_domain()

        return urljoin(domain, url)

    return url


def get_case_view_url(application: ImpOrExp, full_url: bool = False) -> str:
    url_kwargs = {"application_pk": application.pk}
    if application.is_import_application():
        url_kwargs["case_type"] = "import"
    else:
        url_kwargs["case_type"] = "export"
    url = reverse("case:view", kwargs=url_kwargs)
    if full_url:
        return get_full_url(url)
    return url
