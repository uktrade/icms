import copy
import datetime as dt
from typing import Any, ClassVar, final
from uuid import UUID

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage, SafeMIMEMultipart
from django.utils import timezone

from web.domains.case.services import document_pack
from web.domains.case.types import (
    Authority,
    DocumentPack,
    DownloadLink,
    ImpAccessOrExpAccess,
    ImpOrExp,
    ImpOrExpApproval,
)
from web.models import CaseEmail as CaseEmailModel
from web.models import (
    CaseEmailDownloadLink,
    Constabulary,
    ConstabularyLicenceDownloadLink,
    DFLApplication,
    Exporter,
    ExporterContactInvite,
    FurtherInformationRequest,
    Importer,
    ImporterContactInvite,
    Mailshot,
    UpdateRequest,
    User,
    VariationRequest,
    WithdrawApplication,
)
from web.models.shared import ArchiveReasonChoices
from web.permissions import Perms
from web.sites import (
    SiteName,
    get_caseworker_site_domain,
    get_exporter_site_domain,
    get_importer_site_domain,
    is_exporter_site,
    is_importer_site,
)

from .constants import DATE_FORMAT, IMPORT_CASE_EMAILS, EmailTypes
from .models import EmailTemplate
from .types import ImporterDetails
from .url_helpers import (
    get_accept_org_invite_url,
    get_account_recovery_url,
    get_authority_view_url,
    get_case_email_otd_url,
    get_case_manage_view_url,
    get_case_view_url,
    get_dfl_application_otd_url,
    get_exporter_access_request_url,
    get_importer_access_request_url,
    get_importer_view_url,
    get_mailshot_detail_view_url,
    get_maintain_importers_view_url,
    get_manage_access_request_fir_url,
    get_manage_application_fir_url,
    get_respond_to_access_request_fir_url,
    get_respond_to_application_fir_url,
    get_update_request_view_url,
    get_validate_digital_signatures_url,
)


class GOVNotifyEmailMessage(EmailMessage):
    name: ClassVar[EmailTypes]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.template_id = self.get_template_id()

    def get_template_id(self) -> UUID:
        return EmailTemplate.objects.get(name=self.name).gov_notify_template_id

    def message(self) -> SafeMIMEMultipart:
        """Adds the personalisation data to the message header, so it is visible when using the console backend."""
        message = super().message()
        message["Personalisation"] = self.get_personalisation()
        return message

    def get_personalisation(self) -> dict[str, Any]:
        return {
            "icms_url": self.get_site_domain(),
            "icms_contact_email": settings.ILB_CONTACT_EMAIL,
            "icms_contact_phone": settings.ILB_CONTACT_PHONE,
            "subject": self.subject,
            "body": self.body,
            "service_name": self.get_service_name(),
        } | self.get_context()

    def get_context(self) -> dict[str, Any]:
        return {}

    def get_site_domain(self) -> str:
        raise NotImplementedError

    def get_service_name(self) -> str:
        site_domain = self.get_site_domain()
        if site_domain == get_importer_site_domain():
            return SiteName.IMPORTER.label
        if site_domain == get_exporter_site_domain():
            return SiteName.EXPORTER.label
        if site_domain == get_caseworker_site_domain():
            return SiteName.CASEWORKER.label
        raise ValueError(f"Unknown site domain: {site_domain}")


@final
class NewUserWelcomeEmail(GOVNotifyEmailMessage):
    name = EmailTypes.NEW_USER_WELCOME

    def __init__(self, *args: Any, user: User, site: Site, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        self.site = site

    def get_context(self) -> dict[str, Any]:
        site_domain = self.get_site_domain()
        context = {
            "account_recovery_url": get_account_recovery_url(site_domain),
        }

        if is_importer_site(self.site):
            context["organisation_type"] = "Importer"
            context["access_request_url"] = get_importer_access_request_url()
        else:
            context["organisation_type"] = "Exporter"
            context["access_request_url"] = get_exporter_access_request_url()

        return context

    def get_site_domain(self) -> str:
        if is_importer_site(self.site):
            return get_importer_site_domain()
        elif is_exporter_site(self.site):
            return get_exporter_site_domain()

        raise ValueError(f"Unknown site: {self.site}")


class BaseApplicationEmail(GOVNotifyEmailMessage):
    def __init__(self, *args: Any, application: ImpOrExp, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.application = application

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        return context | {
            "reference": self.application.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(self.application, self.get_site_domain()),
        }

    def get_site_domain(self) -> str:
        if self.application.is_import_application():
            return get_importer_site_domain()
        else:
            return get_exporter_site_domain()


class BaseApprovalRequest(GOVNotifyEmailMessage):
    def __init__(self, *args: Any, approval_request: ImpOrExpApproval, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.approval_request = approval_request

    def get_context(self) -> dict[str, Any]:
        access_request = self.approval_request.access_request.get_specific_model()
        return {"user_type": "agent" if access_request.is_agent_request else "user"}


class BaseWithdrawalEmail(GOVNotifyEmailMessage):
    def __init__(self, *args: Any, withdrawal: WithdrawApplication, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.withdrawal = withdrawal
        self.application = withdrawal.export_application or withdrawal.import_application

    def get_context(self) -> dict[str, Any]:
        return {"reference": self.application.reference, "reason": self.withdrawal.reason}

    def get_site_domain(self) -> str:
        if self.withdrawal.import_application:
            return get_importer_site_domain()
        else:
            return get_exporter_site_domain()


class BaseVariationRequestEmail(BaseApplicationEmail):
    def __init__(self, *args: Any, variation_request: VariationRequest, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.variation_request = variation_request


@final
class AccessRequestEmail(GOVNotifyEmailMessage):
    name = EmailTypes.ACCESS_REQUEST

    def __init__(self, *args: Any, access_request: ImpAccessOrExpAccess, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.access_request = access_request

    def get_context(self) -> dict[str, Any]:
        return {"reference": self.access_request.reference}

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class AccessRequestClosedEmail(GOVNotifyEmailMessage):
    name = EmailTypes.ACCESS_REQUEST_CLOSED

    def __init__(self, *args: Any, access_request: ImpAccessOrExpAccess, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.access_request = access_request

    def get_context(self) -> dict[str, Any]:
        return {
            "request_type": self.access_request.REQUEST_TYPE.capitalize(),
            "agent": "Agent " if self.access_request.is_agent_request else "",
            "is_agent": "yes" if self.access_request.is_agent_request else "no",
            "has_been_refused": (
                "yes" if self.access_request.response == self.access_request.REFUSED else "no"
            ),
            "organisation": self.access_request.organisation_name,
            "outcome": self.access_request.get_response_display(),
            "reason": self.get_reason(),
            "service_name": self.get_service_name().lower(),
        }

    def get_reason(self) -> str:
        if not self.access_request.response_reason:
            return ""
        return f"Reason: {self.access_request.response_reason}"

    def get_site_domain(self) -> str:
        match self.access_request.REQUEST_TYPE:
            case "importer":
                return get_importer_site_domain()
            case "exporter":
                return get_exporter_site_domain()
            case _:
                raise ValueError(f"Unknown access request type: {self.access_request.REQUEST_TYPE}")


@final
class ApplicationCompleteEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_COMPLETE


@final
class ApplicationVariationCompleteEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_COMPLETE


@final
class ApplicationExtensionCompleteEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_EXTENSION_COMPLETE


@final
class ApplicationStoppedEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_STOPPED


@final
class ApplicationUpdateResponseEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_UPDATE_RESPONSE

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["application_url"] = get_case_manage_view_url(self.application)
        return context

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class ApplicationRefusedEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_REFUSED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["reason"] = self.application.refuse_reason
        return context


@final
class ExporterAccessRequestApprovalOpenedEmail(BaseApprovalRequest):
    name = EmailTypes.EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED

    def get_site_domain(self) -> str:
        return get_exporter_site_domain()


@final
class ImporterAccessRequestApprovalOpenedEmail(BaseApprovalRequest):
    name = EmailTypes.IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED

    def get_site_domain(self) -> str:
        return get_importer_site_domain()


@final
class WithdrawalOpenedEmail(BaseWithdrawalEmail):
    name = EmailTypes.WITHDRAWAL_OPENED

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class WithdrawalAcceptedEmail(BaseWithdrawalEmail):
    name = EmailTypes.WITHDRAWAL_ACCEPTED


@final
class WithdrawalRejectedEmail(BaseWithdrawalEmail):
    name = EmailTypes.WITHDRAWAL_REJECTED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["reason_rejected"] = self.withdrawal.response
        return context


@final
class WithdrawalCancelledEmail(BaseWithdrawalEmail):
    name = EmailTypes.WITHDRAWAL_CANCELLED

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class ApplicationReassignedEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_REASSIGNED

    def __init__(self, *args: Any, comment: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.comment = comment

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["comment"] = self.comment or "None provided."
        return context

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class ApplicationReopenedEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_REOPENED


@final
class FirearmsSupplementaryReportEmail(BaseApplicationEmail):
    name = EmailTypes.FIREARMS_SUPPLEMENTARY_REPORT


@final
class ConstabularyDeactivatedFirearmsEmail(BaseApplicationEmail):
    name = EmailTypes.CONSTABULARY_DEACTIVATED_FIREARMS

    # Added for clarity
    application: DFLApplication

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if not isinstance(self.application, DFLApplication):
            raise ValueError("Application is not a DFLApplication")

        self.constabulary = self.application.constabulary

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        link = self.generate_view_case_documents_link()
        context["documents_url"] = get_dfl_application_otd_url(link)
        context["check_code"] = str(link.check_code)
        context["constabulary_name"] = self.constabulary.name
        return context

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()

    def get_document_pack(self) -> DocumentPack:
        return document_pack.pack_active_get(self.application)

    def generate_view_case_documents_link(self) -> ConstabularyLicenceDownloadLink:
        if len(self.to) > 1:
            raise ValueError("Unable to create download link for multiple emails.")

        return ConstabularyLicenceDownloadLink.objects.create(
            email=self.to[0],
            constabulary=self.constabulary,
            licence=document_pack.pack_active_get(self.application),
        )


@final
class AccessRequestApprovalCompleteEmail(BaseApprovalRequest):
    name = EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class VariationRequestCancelledEmail(BaseVariationRequestEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["reason"] = self.variation_request.reject_cancellation_reason
        return context

    def get_site_domain(self) -> str:
        if self.variation_request.requested_by.has_perm(Perms.sys.ilb_admin):
            return get_caseworker_site_domain()
        return super().get_site_domain()


@final
class VariationRequestUpdateRequiredEmail(BaseVariationRequestEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["reason"] = self.variation_request.update_request_reason
        return context


@final
class VariationRequestUpdateCancelledEmail(BaseVariationRequestEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED


@final
class VariationRequestUpdateReceivedEmail(BaseVariationRequestEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class VariationRequestRefusedEmail(BaseVariationRequestEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_REFUSED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["reason"] = self.application.variation_refuse_reason
        return context


class BaseCaseEmail(GOVNotifyEmailMessage):
    def __init__(self, *args: Any, case_email: CaseEmailModel, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.case_email = case_email

    def get_site_domain(self) -> str:
        if self.case_email.template_code in IMPORT_CASE_EMAILS:
            return get_importer_site_domain()
        else:
            return get_exporter_site_domain()

    def get_context(self) -> dict[str, Any]:
        return {"subject": self.case_email.subject, "body": self.case_email.body}


@final
class CaseEmail(BaseCaseEmail):
    name = EmailTypes.CASE_EMAIL


@final
class CaseEmailWithDocuments(BaseCaseEmail):
    name = EmailTypes.CASE_EMAIL_WITH_DOCUMENTS

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        link = self.generate_documents_download_link()

        return context | {
            "documents_url": (link and get_case_email_otd_url(link)) or "",
            "check_code": (link and str(link.check_code)) or "",
        }

    def generate_documents_download_link(self) -> DownloadLink | None:
        if not self.case_email.attachments.exists():
            return None

        return CaseEmailDownloadLink.objects.create(case_email=self.case_email, email=self.to[0])


class BaseFurtherInformationRequestEmail(GOVNotifyEmailMessage):
    def __init__(self, *args: Any, fir: FurtherInformationRequest, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fir = fir

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["subject"] = self.fir.request_subject
        context["body"] = self.fir.request_detail
        return context


class BaseApplicationFurtherInformationRequestEmail(
    BaseApplicationEmail, BaseFurtherInformationRequestEmail
):
    name = EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST

    def get_context(self) -> dict[str, Any]:
        context = super().get_context() | {"fir_type": "case"}
        return context


@final
class ApplicationFurtherInformationRequestEmail(BaseApplicationFurtherInformationRequestEmail):
    name = EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST

    def get_context(self) -> dict[str, Any]:
        context = super().get_context() | {
            "fir_url": get_respond_to_application_fir_url(self.application, self.fir),
        }
        return context


class BaseAccessRequestFurtherInformationRequestEmail(BaseFurtherInformationRequestEmail):

    def __init__(self, *args: Any, access_request: ImpAccessOrExpAccess, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.access_request = access_request

    def get_context(self) -> dict[str, Any]:
        context = super().get_context() | {
            "reference": self.access_request.reference,
            "fir_type": "access request",
        }
        return context

    def get_site_domain(self) -> str:
        access_request = self.access_request.get_specific_model()
        match access_request.REQUEST_TYPE:
            case "importer":
                return get_importer_site_domain()
            case "exporter":
                return get_exporter_site_domain()
            case _:
                raise ValueError(f"Unknown access request type: {access_request.REQUEST_TYPE}")


@final
class AccessRequestFurtherInformationRequestEmail(BaseAccessRequestFurtherInformationRequestEmail):
    name = EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST

    def get_context(self) -> dict[str, Any]:
        context = super().get_context() | {
            "fir_url": get_respond_to_access_request_fir_url(
                self.get_site_domain(), self.fir, self.access_request
            ),
        }
        return context


@final
class AccessRequestFurtherInformationRequestRespondedEmail(
    BaseAccessRequestFurtherInformationRequestEmail
):
    name = EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context() | {
            "fir_url": get_manage_access_request_fir_url(self.access_request),
        }
        return context

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class AccessRequestFurtherInformationRequestWithdrawnEmail(
    BaseAccessRequestFurtherInformationRequestEmail
):
    name = EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN


@final
class ApplicationFurtherInformationRequestRespondedEmail(
    BaseApplicationFurtherInformationRequestEmail
):
    name = EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context() | {
            "fir_url": get_manage_application_fir_url(self.application),
        }
        return context

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class ApplicationFurtherInformationRequestWithdrawnEmail(
    BaseApplicationFurtherInformationRequestEmail
):
    name = EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN


@final
class LicenceRevokedEmail(BaseApplicationEmail):
    name = EmailTypes.LICENCE_REVOKED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context() | {
            "licence_number": self.get_licence_number(),
        }
        return context

    def get_licence_number(self) -> str:
        pack = document_pack.pack_revoked_get(self.application)
        return document_pack.doc_ref_licence_get(pack).reference


@final
class CertificateRevokedEmail(BaseApplicationEmail):
    name = EmailTypes.CERTIFICATE_REVOKED

    def get_context(self) -> dict[str, Any]:
        context = super().get_context() | {
            "certificate_references": ",".join(self.get_certificate_references()),
        }
        return context

    def get_certificate_references(self) -> list[str]:
        pack = document_pack.pack_revoked_get(self.application)
        return list(
            document_pack.doc_ref_certificates_all(pack).values_list("reference", flat=True)
        )


@final
class ApplicationUpdateEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_UPDATE

    def __init__(self, *args: Any, update_request: UpdateRequest, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update_request = update_request

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["subject"] = self.update_request.request_subject
        context["body"] = self.update_request.request_detail
        context["application_update_url"] = get_update_request_view_url(
            self.application, self.update_request, self.get_site_domain()
        )
        return context


@final
class ApplicationUpdateWithdrawnEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_UPDATE_WITHDRAWN


@final
class AuthorityArchivedEmail(GOVNotifyEmailMessage):
    name = EmailTypes.AUTHORITY_ARCHIVED

    def __init__(self, *args: Any, authority: Authority, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.authority = authority

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        return context | {
            "authority_name": self.authority.reference,
            "authority_type": self.authority.AUTHORITY_TYPE,
            "authority_url": get_authority_view_url(self.authority, full_url=True),
            "date": timezone.now().strftime(DATE_FORMAT),
            "importer_url": get_importer_view_url(self.authority.importer, full_url=True),
            "importer_name": self.authority.importer.name,
            "reason": self.get_reason(),
            "reason_other": self.authority.other_archive_reason or "",
        }

    def get_reason(self) -> str:
        reasons = copy.copy(self.authority.archive_reason)
        if ArchiveReasonChoices.OTHER in reasons:
            reasons.remove(ArchiveReasonChoices.OTHER)
        return "\r\n".join([reason.title() for reason in reasons])

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


class BaseAuthorityExpiringEmail(GOVNotifyEmailMessage):
    def __init__(
        self,
        *args: Any,
        importers_details: list[ImporterDetails],
        authority_type: str,
        expiry_date: dt.date,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.importers_details = importers_details
        self.authority_type = authority_type
        self.expiry_date = expiry_date

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        return context | {
            "importers_count": len(self.importers_details),
            "authority_type": self.authority_type,
            "summary_text": self.get_summary_text(),
            "expiry_date": self.expiry_date.strftime(DATE_FORMAT),
            "maintain_importers_url": get_maintain_importers_view_url(),
        }

    def get_summary_text(self) -> str:
        summary_text = []
        for importer in self.importers_details:
            summary_text.append(
                f"Importer name: {importer['name']}\r\n"
                f"Importer ID: {importer['id']}\r\n"
                f"{self.authority_type} references(s): {importer['authority_refs']}\r\n"
            )
        return "\r\n".join(summary_text)

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class Section5AuthorityExpiringEmail(BaseAuthorityExpiringEmail):
    name = EmailTypes.AUTHORITY_EXPIRING_SECTION_5


@final
class FirearmsAuthorityExpiringEmail(BaseAuthorityExpiringEmail):
    name = EmailTypes.AUTHORITY_EXPIRING_FIREARMS

    def __init__(self, *args: Any, constabulary: Constabulary, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.constabulary = constabulary

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        return context | {"constabulary_name": self.constabulary.name}


class BaseMailshotEmail(GOVNotifyEmailMessage):
    def __init__(self, *args: Any, mailshot: Mailshot, site_domain: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.mailshot = mailshot
        self.site_domain = site_domain

    def get_context(self) -> dict[str, Any]:
        context = super().get_context()
        context["subject"] = self.get_subject()
        context["body"] = self.get_body()
        context["mailshot_url"] = get_mailshot_detail_view_url(self.mailshot, self.site_domain)
        return context

    def get_subject(self) -> str:
        raise NotImplementedError

    def get_body(self) -> str:
        raise NotImplementedError

    def get_site_domain(self) -> str:
        return self.site_domain


@final
class MailshotEmail(BaseMailshotEmail):
    name = EmailTypes.MAILSHOT

    def get_subject(self) -> str:
        return self.mailshot.email_subject

    def get_body(self) -> str:
        return self.mailshot.email_body


@final
class RetractMailshotEmail(BaseMailshotEmail):
    name = EmailTypes.RETRACT_MAILSHOT

    def get_subject(self) -> str:
        return self.mailshot.retract_email_subject

    def get_body(self) -> str:
        return self.mailshot.retract_email_body


@final
class OrganisationContactInviteEmail(GOVNotifyEmailMessage):
    name = EmailTypes.ORG_CONTACT_INVITE

    def __init__(
        self,
        *args: Any,
        organisation: Importer | Exporter,
        invite: ImporterContactInvite | ExporterContactInvite,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.organisation = organisation
        self.invite = invite

    def get_context(self) -> dict[str, Any]:
        # importer display_name or name (common to exporter and importer)
        org = self.invite.organisation
        organisation_name = getattr(org, "display_name", org.name)

        return {
            "organisation_name": organisation_name,
            "first_name": self.invite.first_name,
            "last_name": self.invite.last_name,
            "invited_by": self.invite.invited_by.full_name,
            "accept_invite_url": get_accept_org_invite_url(self.organisation, self.invite),
        }

    def get_site_domain(self) -> str:
        match self.organisation:
            case Importer():
                return get_importer_site_domain()
            case Exporter():
                return get_exporter_site_domain()
            case _:
                raise ValueError(f"Unknown organisation: {self.organisation}")
