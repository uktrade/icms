from urllib.parse import urljoin

from django.shortcuts import reverse
from django.templatetags.static import static

from web.domains.case.types import ImpOrExp
from web.sites import get_importer_site_domain


def get_validate_digital_signatures_url(full_url: bool = False) -> str:
    url = static("web/docs/ValidateDigSigs.pdf")
    if full_url:
        return urljoin(get_importer_site_domain(), url)
    return url


def get_case_view_url(application: ImpOrExp, domain: str) -> str:
    url_kwargs = {"application_pk": application.pk}
    if application.is_import_application():
        url_kwargs["case_type"] = "import"
    else:
        url_kwargs["case_type"] = "export"
    return urljoin(domain, reverse("case:view", kwargs=url_kwargs))
