from urllib.parse import urljoin

from django.http import QueryDict
from django.shortcuts import reverse

from web.domains.case.types import Authority, DocumentPack, ImpOrExp
from web.models import (
    AccessRequest,
    CaseDocumentReference,
    CaseEmailDownloadLink,
    ConstabularyLicenceDownloadLink,
    DFLApplication,
    EmailVerification,
    Exporter,
    ExporterContactInvite,
    FirearmsAuthority,
    FurtherInformationRequest,
    ImportApplication,
    Importer,
    ImporterContactInvite,
    Mailshot,
    UpdateRequest,
)
from web.sites import (
    get_caseworker_site_domain,
    get_exporter_site_domain,
    get_importer_site_domain,
)


def get_validate_digital_signatures_url(domain: str) -> str:
    return urljoin(domain, reverse("support:validate-signature"))


def get_case_view_url(application: ImpOrExp, domain: str) -> str:
    url_kwargs = {"application_pk": application.pk}
    if application.is_import_application():
        url_kwargs["case_type"] = "import"
    else:
        url_kwargs["case_type"] = "export"
    return urljoin(domain, reverse("case:view", kwargs=url_kwargs))


def get_case_manage_view_url(application: ImpOrExp) -> str:
    url_kwargs = {"application_pk": application.pk}
    if application.is_import_application():
        url_kwargs["case_type"] = "import"
    else:
        url_kwargs["case_type"] = "export"
    return urljoin(get_caseworker_site_domain(), reverse("case:manage", kwargs=url_kwargs))


def get_update_request_view_url(
    application: ImpOrExp, update_request: UpdateRequest, domain: str
) -> str:
    url_kwargs = {"application_pk": application.pk, "update_request_pk": update_request.pk}
    if application.is_import_application():
        url_kwargs["case_type"] = "import"
    else:
        url_kwargs["case_type"] = "export"
    return urljoin(domain, reverse("case:start-update-request", kwargs=url_kwargs))


def get_importer_view_url(importer: Importer, full_url: bool = False) -> str:
    url = reverse("importer-view", kwargs={"pk": importer.pk})
    if full_url:
        return urljoin(get_caseworker_site_domain(), url)
    return url


def get_authority_view_url(authority: Authority, full_url: bool = False) -> str:
    if authority.AUTHORITY_TYPE == FirearmsAuthority.AUTHORITY_TYPE:
        view_name = "importer-firearms-view"
    else:
        view_name = "importer-section5-view"

    url = reverse(view_name, kwargs={"pk": authority.pk})
    if full_url:
        return urljoin(get_caseworker_site_domain(), url)
    return url


def get_mailshot_detail_view_url(mailshot: Mailshot, domain: str) -> str:
    return urljoin(domain, reverse("mailshot-detail-received", kwargs={"mailshot_pk": mailshot.pk}))


def get_maintain_importers_view_url() -> str:
    return urljoin(get_caseworker_site_domain(), reverse("importer-list"))


# NOTE: Not currently used (as constabulary contacts don't log in to ICMS)
def get_constabulary_document_view_url(
    application: DFLApplication, doc_pack: DocumentPack, full_url: bool = False
) -> str:
    url_kwargs = {
        "application_pk": application.pk,
        "doc_pack_pk": doc_pack.pk,
        "case_type": "import",
    }
    url = reverse("case:constabulary-doc", kwargs=url_kwargs)
    if full_url:
        return urljoin(get_caseworker_site_domain(), url)
    return url


def get_constabulary_document_download_view_url(
    application: ImportApplication,
    doc_pack: DocumentPack,
    cdr: CaseDocumentReference,
    full_url: bool = False,
) -> str:
    url_kwargs = {
        "application_pk": application.pk,
        "doc_pack_pk": doc_pack.pk,
        "case_type": "import",
        "cdr_pk": cdr.pk,
    }
    url = reverse("case:constabulary-doc-download", kwargs=url_kwargs)
    if full_url:
        return urljoin(get_caseworker_site_domain(), url)
    return url


def get_account_recovery_url(site_domain: str) -> str:
    return urljoin(site_domain, reverse("account-recovery"))


def get_importer_access_request_url() -> str:
    return urljoin(get_importer_site_domain(), reverse("access:importer-request"))


def get_exporter_access_request_url() -> str:
    return urljoin(get_exporter_site_domain(), reverse("access:exporter-request"))


def get_accept_org_invite_url(
    org: Importer | Exporter, invite: ImporterContactInvite | ExporterContactInvite
) -> str:
    match org:
        case Importer():
            site_url = get_importer_site_domain()
        case Exporter():
            site_url = get_exporter_site_domain()
        case _:
            raise ValueError(f"Unknown organisation: {org}")

    return urljoin(site_url, reverse("contacts:accept-org-invite", kwargs={"code": invite.code}))


def get_dfl_application_otd_url(link: ConstabularyLicenceDownloadLink) -> str:
    qd = QueryDict(mutable=True)
    qd.update(
        {
            "email": link.email,
            "constabulary": link.constabulary.pk,
            "check_code": link.check_code,
        }
    )

    return urljoin(
        get_caseworker_site_domain(),
        reverse("case:download-dfl-case-documents", kwargs={"code": link.code})
        + f"?{qd.urlencode()}",
    )


def get_case_email_otd_url(link: CaseEmailDownloadLink) -> str:
    qd = QueryDict(mutable=True)
    qd.update(
        {
            "email": link.email,
            "check_code": link.check_code,
        }
    )

    return urljoin(
        get_caseworker_site_domain(),
        reverse("case:download-case-email-documents", kwargs={"code": link.code})
        + f"?{qd.urlencode()}",
    )


def get_respond_to_application_fir_url(
    application: ImpOrExp, fir: FurtherInformationRequest
) -> str:
    if application.is_import_application():
        case_type = "import"
        site_url = get_importer_site_domain()
    else:
        case_type = "export"
        site_url = get_exporter_site_domain()
    kwargs = {"application_pk": application.pk, "fir_pk": fir.pk, "case_type": case_type}
    return urljoin(site_url, reverse("case:respond-fir", kwargs=kwargs))


def get_respond_to_access_request_fir_url(
    site_url: str, fir: FurtherInformationRequest, access_request: AccessRequest
) -> str:
    return urljoin(
        site_url,
        reverse(
            "case:respond-fir",
            kwargs={"application_pk": access_request.pk, "fir_pk": fir.pk, "case_type": "access"},
        ),
    )


def get_manage_application_fir_url(application: ImpOrExp) -> str:
    if application.is_import_application():
        case_type = "import"
    else:
        case_type = "export"
    kwargs = {"application_pk": application.pk, "case_type": case_type}
    return urljoin(get_caseworker_site_domain(), reverse("case:manage-firs", kwargs=kwargs))


def get_manage_access_request_fir_url(access_request: AccessRequest) -> str:
    return urljoin(
        get_caseworker_site_domain(),
        reverse(
            "case:manage-firs", kwargs={"application_pk": access_request.pk, "case_type": "access"}
        ),
    )


def get_email_verification_url(verification: EmailVerification, domain: str) -> str:
    return urljoin(domain, verification.get_email_verification_url())
