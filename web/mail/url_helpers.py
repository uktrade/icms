from urllib.parse import urljoin

from django.shortcuts import reverse
from django.templatetags.static import static

from web.domains.case.types import ImpOrExp
from web.sites import (
    get_caseworker_site_domain,
    get_exporter_site_domain,
    get_importer_site_domain,
)


def get_validate_digital_signatures_url(full_url: bool = False) -> str:
    url = static("web/docs/ValidateDigSigs.pdf")
    if full_url:
        domain = get_caseworker_site_domain()

        return urljoin(domain, url)

    return url


def get_case_view_url(application: ImpOrExp, full_url: bool = False) -> str:
    url_kwargs = {"application_pk": application.pk}

    if application.is_import_application():
        # TODO: ICMSLST-2313 Check if we ever need to send this to the caseworker domain
        domain = get_importer_site_domain()
        url_kwargs["case_type"] = "import"
    else:
        # TODO: ICMSLST-2313 Check if we ever need to send this to the caseworker domain
        domain = get_exporter_site_domain()
        url_kwargs["case_type"] = "export"

    url = reverse("case:view", kwargs=url_kwargs)

    if full_url:
        return urljoin(domain, url)

    return url
