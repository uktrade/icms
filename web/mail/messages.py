import copy
from typing import ClassVar, final
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMessage, SafeMIMEMultipart
from django.utils import timezone

from web.domains.case.services import document_pack
from web.domains.case.types import (
    Authority,
    ImpAccessOrExpAccess,
    ImpOrExp,
    ImpOrExpApproval,
)
from web.models import CaseEmail as CaseEmailModel
from web.models import (
    FurtherInformationRequest,
    UpdateRequest,
    VariationRequest,
    WithdrawApplication,
)
from web.models.shared import ArchiveReasonChoices
from web.permissions import Perms
from web.sites import (
    get_caseworker_site_domain,
    get_exporter_site_domain,
    get_importer_site_domain,
)

from .constants import IMPORT_CASE_EMAILS, EmailTypes
from .models import EmailTemplate
from .url_helpers import (
    get_authority_view_url,
    get_case_view_url,
    get_importer_view_url,
    get_validate_digital_signatures_url,
)


class GOVNotifyEmailMessage(EmailMessage):
    name: ClassVar[EmailTypes]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_id = self.get_template_id()

    def message(self) -> SafeMIMEMultipart:
        """Adds the personalisation data to the message header, so it is visible when using the console backend."""
        message = super().message()
        message["Personalisation"] = self.get_personalisation()
        return message

    def get_context(self) -> dict:
        return {}

    def get_personalisation(self) -> dict:
        return {
            "icms_url": self.get_site_domain(),
            "icms_contact_email": settings.ILB_CONTACT_EMAIL,
            "icms_contact_phone": settings.ILB_CONTACT_PHONE,
            "subject": self.subject,
            "body": self.body,
        } | self.get_context()

    def get_template_id(self) -> UUID:
        return EmailTemplate.objects.get(name=self.name).gov_notify_template_id

    def get_site_domain(self) -> str:
        raise NotImplementedError


class BaseApplicationEmail(GOVNotifyEmailMessage):
    def __init__(self, *args, application: ImpOrExp, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application

    def get_context(self) -> dict:
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
    def __init__(self, *args, approval_request: ImpOrExpApproval, **kwargs):
        super().__init__(*args, **kwargs)
        self.approval_request = approval_request

    def get_context(self) -> dict:
        access_request = self.approval_request.access_request.get_specific_model()
        return {"user_type": "agent" if access_request.is_agent_request else "user"}


class BaseWithdrawalEmail(GOVNotifyEmailMessage):
    def __init__(self, *args, withdrawal: WithdrawApplication, **kwargs):
        super().__init__(*args, **kwargs)
        self.withdrawal = withdrawal
        self.application = withdrawal.export_application or withdrawal.import_application

    def get_context(self) -> dict:
        return {"reference": self.application.reference, "reason": self.withdrawal.reason}

    def get_site_domain(self) -> str:
        if self.withdrawal.import_application:
            return get_importer_site_domain()
        else:
            return get_exporter_site_domain()


class BaseVariationRequestEmail(BaseApplicationEmail):
    def __init__(self, *args, variation_request: VariationRequest, **kwargs):
        super().__init__(*args, **kwargs)
        self.variation_request = variation_request


@final
class AccessRequestEmail(GOVNotifyEmailMessage):
    name = EmailTypes.ACCESS_REQUEST

    def __init__(self, *args, access_request: ImpAccessOrExpAccess, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_request = access_request

    def get_context(self) -> dict:
        return {"reference": self.access_request.reference}

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class AccessRequestClosedEmail(GOVNotifyEmailMessage):
    name = EmailTypes.ACCESS_REQUEST_CLOSED

    def __init__(self, *args, access_request: ImpAccessOrExpAccess, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_request = access_request

    def get_context(self) -> dict:
        return {
            "request_type": self.access_request.REQUEST_TYPE.capitalize(),
            "agent": "Agent " if self.access_request.is_agent_request else "",
            "organisation": self.access_request.organisation_name,
            "outcome": self.access_request.get_response_display(),
            "reason": self.get_reason(),
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


@final
class ApplicationRefusedEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_REFUSED

    def get_context(self) -> dict:
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

    def get_context(self) -> dict:
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

    def __init__(self, *args, comment: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.comment = comment

    def get_context(self) -> dict:
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
class AccessRequestApprovalCompleteEmail(BaseApprovalRequest):
    name = EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE

    def get_site_domain(self) -> str:
        return get_caseworker_site_domain()


@final
class VariationRequestCancelledEmail(BaseVariationRequestEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED

    def get_context(self) -> dict:
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

    def get_context(self) -> dict:
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

    def get_context(self) -> dict:
        context = super().get_context()
        context["reason"] = self.application.variation_refuse_reason
        return context


@final
class CaseEmail(GOVNotifyEmailMessage):
    name = EmailTypes.CASE_EMAIL

    def __init__(self, *args, case_email: CaseEmailModel, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_email = case_email

    def get_site_domain(self) -> str:
        if self.case_email.template_code in IMPORT_CASE_EMAILS:
            return get_importer_site_domain()
        else:
            return get_exporter_site_domain()

    def get_context(self) -> dict:
        return {"subject": self.case_email.subject, "body": self.case_email.body}


class BaseFurtherInformationRequestEmail(GOVNotifyEmailMessage):
    def __init__(self, *args, fir: FurtherInformationRequest, **kwargs):
        super().__init__(*args, **kwargs)
        self.fir = fir

    def get_context(self) -> dict:
        context = super().get_context()
        context["subject"] = self.fir.request_subject
        context["body"] = self.fir.request_detail
        return context


class ApplicationFurtherInformationRequestEmail(
    BaseApplicationEmail, BaseFurtherInformationRequestEmail
):
    name = EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST

    def get_context(self) -> dict:
        context = super().get_context() | {"fir_type": "case"}
        return context


class AccessRequestFurtherInformationRequestEmail(BaseFurtherInformationRequestEmail):
    name = EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST

    def __init__(self, *args, access_request: ImpAccessOrExpAccess, **kwargs):
        self.access_request = access_request
        super().__init__(*args, **kwargs)

    def get_context(self) -> dict:
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
class AccessRequestFurtherInformationRequestRespondedEmail(
    AccessRequestFurtherInformationRequestEmail
):
    name = EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED


@final
class AccessRequestFurtherInformationRequestWithdrawnEmail(
    AccessRequestFurtherInformationRequestEmail
):
    name = EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN


@final
class ApplicationFurtherInformationRequestRespondedEmail(ApplicationFurtherInformationRequestEmail):
    name = EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED


@final
class ApplicationFurtherInformationRequestWithdrawnEmail(ApplicationFurtherInformationRequestEmail):
    name = EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN


@final
class LicenceRevokedEmail(BaseApplicationEmail):
    name = EmailTypes.LICENCE_REVOKED

    def get_context(self) -> dict:
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

    def get_context(self) -> dict:
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

    def __init__(self, *args, update_request: UpdateRequest, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_request = update_request

    def get_context(self) -> dict:
        context = super().get_context()
        context["subject"] = self.update_request.request_subject
        context["body"] = self.update_request.request_detail
        return context


@final
class AuthorityArchivedEmail(GOVNotifyEmailMessage):
    name = EmailTypes.AUTHORITY_ARCHIVED

    def __init__(self, *args, authority: Authority, **kwargs):
        super().__init__(*args, **kwargs)
        self.authority = authority

    def get_context(self) -> dict:
        context = super().get_context()
        return context | {
            "authority_name": self.authority.reference,
            "authority_type": self.authority.AUTHORITY_TYPE,
            "authority_url": get_authority_view_url(self.authority, full_url=True),
            "date": timezone.now().strftime("%-d %B %Y"),
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
