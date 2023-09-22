from typing import ClassVar, final
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMessage, SafeMIMEMultipart

from web.domains.case.types import ImpAccessOrExpAccess, ImpOrExp, ImpOrExpApproval
from web.models import VariationRequest, WithdrawApplication
from web.sites import get_caseworker_site_domain

from .constants import EmailTypes
from .models import EmailTemplate
from .url_helpers import get_case_view_url, get_validate_digital_signatures_url


class GOVNotifyEmailMessage(EmailMessage):
    name: ClassVar[EmailTypes]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_id = self.get_template_id()
        self.personalisation = self.get_personalisation()

    def message(self) -> SafeMIMEMultipart:
        """Adds the personalisation data to the message header, so it is visible when using the console backend."""
        message = super().message()
        message["Personalisation"] = self.personalisation
        return message

    def get_context(self) -> dict:
        raise NotImplementedError

    def get_personalisation(self) -> dict:
        return {
            # TODO: ICMSLST-2313 Revisit this as it will change depending on the email type.
            "icms_url": get_caseworker_site_domain(),
            "icms_contact_email": settings.ILB_CONTACT_EMAIL,
            "icms_contact_phone": settings.ILB_CONTACT_PHONE,
            "subject": self.subject,
            "body": self.body,
        } | self.get_context()

    def get_template_id(self) -> UUID:
        return EmailTemplate.objects.get(name=self.name).gov_notify_template_id


class BaseApplicationEmail(GOVNotifyEmailMessage):
    def __init__(self, *args, application: ImpOrExp, **kwargs):
        self.application = application
        super().__init__(*args, **kwargs)

    def get_context(self) -> dict:
        return {
            "reference": self.application.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(self.application, full_url=True),
        }


class BaseApprovalRequest(GOVNotifyEmailMessage):
    def __init__(self, *args, approval_request: ImpOrExpApproval, **kwargs):
        self.approval_request = approval_request
        super().__init__(*args, **kwargs)

    def get_context(self) -> dict:
        access_request = self.approval_request.access_request.get_specific_model()
        return {"user_type": "agent" if access_request.is_agent_request else "user"}


class BaseWithdrawalEmail(GOVNotifyEmailMessage):
    def __init__(self, *args, withdrawal: WithdrawApplication, **kwargs):
        self.withdrawal = withdrawal
        self.application = withdrawal.export_application or withdrawal.import_application
        super().__init__(*args, **kwargs)

    def get_context(self) -> dict:
        return {"reference": self.application.reference, "reason": self.withdrawal.reason}


class BaseVariationRequestEmail(BaseApplicationEmail):
    def __init__(self, *args, variation_request: VariationRequest, **kwargs):
        self.variation_request = variation_request
        super().__init__(*args, **kwargs)


@final
class AccessRequestEmail(GOVNotifyEmailMessage):
    name = EmailTypes.ACCESS_REQUEST

    def __init__(self, *args, access_request: ImpAccessOrExpAccess, **kwargs):
        self.access_request = access_request
        super().__init__(*args, **kwargs)

    def get_context(self) -> dict:
        return {"reference": self.access_request.reference}


@final
class AccessRequestClosedEmail(GOVNotifyEmailMessage):
    name = EmailTypes.ACCESS_REQUEST_CLOSED

    def __init__(self, *args, access_request: ImpAccessOrExpAccess, **kwargs):
        self.access_request = access_request
        super().__init__(*args, **kwargs)

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
class ApplicationRefusedEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_REFUSED

    def get_context(self) -> dict:
        context = super().get_context()
        context["reason"] = self.application.refuse_reason
        return context


@final
class ExporterAccessRequestApprovalOpenedEmail(BaseApprovalRequest):
    name = EmailTypes.EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED


@final
class ImporterAccessRequestApprovalOpenedEmail(BaseApprovalRequest):
    name = EmailTypes.IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED


@final
class WithdrawalOpenedEmail(BaseWithdrawalEmail):
    name = EmailTypes.WITHDRAWAL_OPENED


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


@final
class ApplicationReassignedEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_REASSIGNED

    def __init__(self, *args, comment: str, **kwargs):
        self.comment = comment
        super().__init__(*args, **kwargs)

    def get_context(self) -> dict:
        context = super().get_context()
        context["comment"] = self.comment or "None provided."
        return context


@final
class ApplicationReopenedEmail(BaseApplicationEmail):
    name = EmailTypes.APPLICATION_REOPENED


@final
class FirearmsSupplementaryReportEmail(BaseApplicationEmail):
    name = EmailTypes.FIREARMS_SUPPLEMENTARY_REPORT


@final
class AccessRequestApprovalCompleteEmail(BaseApprovalRequest):
    name = EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE


@final
class VariationRequestCancelledEmail(BaseVariationRequestEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED

    def get_context(self) -> dict:
        context = super().get_context()
        context["reason"] = self.variation_request.reject_cancellation_reason
        return context


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


@final
class VariationRequestRefusedEmail(BaseVariationRequestEmail):
    name = EmailTypes.APPLICATION_VARIATION_REQUEST_REFUSED

    def get_context(self) -> dict:
        context = super().get_context()
        context["reason"] = self.application.variation_refuse_reason
        return context
