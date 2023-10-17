from django.db.models import QuerySet
from django.utils import timezone

from web.domains.case.types import ImpAccessOrExpAccess, ImpOrExp, ImpOrExpApproval
from web.domains.template.utils import get_email_template_subject_body
from web.flow.models import ProcessTypes
from web.models import CaseEmail as CaseEmailModel
from web.models import (
    ExportApplication,
    ExporterApprovalRequest,
    FurtherInformationRequest,
    ImportApplication,
    ImporterApprovalRequest,
    UpdateRequest,
    VariationRequest,
    WithdrawApplication,
)
from web.notify import notify

from .constants import CaseEmailTemplate, VariationRequestDescription
from .messages import (
    AccessRequestApprovalCompleteEmail,
    AccessRequestClosedEmail,
    AccessRequestEmail,
    AccessRequestFurtherInformationRequestEmail,
    AccessRequestFurtherInformationRequestRespondedEmail,
    AccessRequestFurtherInformationRequestWithdrawnEmail,
    ApplicationCompleteEmail,
    ApplicationExtensionCompleteEmail,
    ApplicationFurtherInformationRequestEmail,
    ApplicationFurtherInformationRequestRespondedEmail,
    ApplicationFurtherInformationRequestWithdrawnEmail,
    ApplicationReassignedEmail,
    ApplicationRefusedEmail,
    ApplicationReopenedEmail,
    ApplicationStoppedEmail,
    ApplicationUpdateEmail,
    ApplicationUpdateResponseEmail,
    ApplicationVariationCompleteEmail,
    CaseEmail,
    CertificateRevokedEmail,
    ExporterAccessRequestApprovalOpenedEmail,
    FirearmsSupplementaryReportEmail,
    ImporterAccessRequestApprovalOpenedEmail,
    LicenceRevokedEmail,
    VariationRequestCancelledEmail,
    VariationRequestRefusedEmail,
    VariationRequestUpdateCancelledEmail,
    VariationRequestUpdateReceivedEmail,
    VariationRequestUpdateRequiredEmail,
    WithdrawalAcceptedEmail,
    WithdrawalCancelledEmail,
    WithdrawalOpenedEmail,
    WithdrawalRejectedEmail,
)
from .recipients import (
    get_application_contact_email_addresses,
    get_case_officers_email_addresses,
    get_email_addresses_for_case_email,
    get_email_addresses_for_users,
    get_ilb_case_officers_email_addresses,
    get_organisation_contact_email_addresses,
)


def send_access_requested_email(access_request: ImpAccessOrExpAccess) -> None:
    recipients = get_ilb_case_officers_email_addresses()
    for recipient in recipients:
        AccessRequestEmail(access_request=access_request, to=[recipient]).send()


def send_access_request_closed_email(access_request: ImpAccessOrExpAccess) -> None:
    recipients = get_email_addresses_for_users([access_request.submitted_by])
    for recipient in recipients:
        AccessRequestClosedEmail(access_request=access_request, to=[recipient]).send()


def send_completed_application_email(application: ImpOrExp) -> None:
    variations = application.variation_requests.filter(
        status__in=[VariationRequest.Statuses.ACCEPTED, VariationRequest.Statuses.CLOSED]
    )

    if variations.filter(extension_flag=True).exists():
        send_application_extension_complete_email(application)
    elif variations.exists():
        send_application_variation_complete_email(application)
    else:
        send_application_complete_email(application)


def send_application_extension_complete_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationExtensionCompleteEmail(application=application, to=[recipient]).send()


def send_application_variation_complete_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationVariationCompleteEmail(application=application, to=[recipient]).send()


def send_application_complete_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationCompleteEmail(application=application, to=[recipient]).send()


def send_completed_application_process_notifications(application: ImpOrExp) -> None:
    if application.process_type == ProcessTypes.FA_DFL:
        # TODO: ICMSLST-2145 Update to use GOV Notify
        notify.send_constabulary_deactivated_firearms_notification(application.dflapplication)

    if application.process_type in [ProcessTypes.FA_DFL, ProcessTypes.FA_OIL, ProcessTypes.FA_SIL]:
        send_firearms_supplementary_report_email(application)

    send_completed_application_email(application)


def send_application_stopped_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationStoppedEmail(application=application, to=[recipient]).send()


def send_application_refused_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationRefusedEmail(application=application, to=[recipient]).send()


def send_approval_request_opened_email(approval_request: ImpOrExpApproval) -> None:
    if approval_request.access_request.process_type == ProcessTypes.EAR:
        send_exporter_approval_request_opened_email(approval_request)
    else:
        send_importer_approval_request_opened_email(approval_request)


def send_exporter_approval_request_opened_email(approval_request: ExporterApprovalRequest) -> None:
    org = approval_request.access_request.get_specific_model().link
    recipients = get_organisation_contact_email_addresses(org)
    for recipient in recipients:
        ExporterAccessRequestApprovalOpenedEmail(
            approval_request=approval_request, to=[recipient]
        ).send()


def send_importer_approval_request_opened_email(approval_request: ImporterApprovalRequest) -> None:
    org = approval_request.access_request.get_specific_model().link
    recipients = get_organisation_contact_email_addresses(org)
    for recipient in recipients:
        ImporterAccessRequestApprovalOpenedEmail(
            approval_request=approval_request, to=[recipient]
        ).send()


def send_approval_request_completed_email(approval_request: ImpOrExpApproval) -> None:
    recipients = get_ilb_case_officers_email_addresses()
    for recipient in recipients:
        AccessRequestApprovalCompleteEmail(approval_request=approval_request, to=[recipient]).send()


def send_withdrawal_email(withdrawal: WithdrawApplication) -> None:
    match withdrawal.status:
        case WithdrawApplication.Statuses.OPEN:
            send_withdrawal_opened_email(withdrawal)
        case WithdrawApplication.Statuses.ACCEPTED:
            send_withdrawal_accepted_email(withdrawal)
        case WithdrawApplication.Statuses.REJECTED:
            send_withdrawal_rejected_email(withdrawal)
        case WithdrawApplication.Statuses.DELETED:
            send_withdrawal_cancelled_email(withdrawal)
        case _:
            raise ValueError("Unsupported Withdrawal Status")


def send_variation_request_email(
    variation_request: VariationRequest,
    description: VariationRequestDescription,
    application: ImpOrExp,
) -> None:
    match description:
        case VariationRequestDescription.CANCELLED:
            send_variation_request_cancelled_email(variation_request, application)
        case VariationRequestDescription.UPDATE_REQUIRED:
            send_variation_request_update_required_email(variation_request, application)
        case VariationRequestDescription.UPDATE_CANCELLED:
            send_variation_request_update_cancelled_email(variation_request, application)
        case VariationRequestDescription.UPDATE_RECEIVED:
            send_variation_request_update_received_email(variation_request, application)
        case VariationRequestDescription.REFUSED:
            send_variation_request_refused_email(variation_request, application)
        case _:
            raise ValueError("Unsupported Variation Request Description")


def send_variation_request_cancelled_email(
    variation_request: VariationRequest, application: ImpOrExp
) -> None:
    recipients = get_email_addresses_for_users([variation_request.requested_by])
    for recipient in recipients:
        VariationRequestCancelledEmail(
            application=application, variation_request=variation_request, to=[recipient]
        ).send()


def send_variation_request_update_required_email(
    variation_request: VariationRequest, application: ImpOrExp
) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        VariationRequestUpdateRequiredEmail(
            application=application, variation_request=variation_request, to=[recipient]
        ).send()


def send_variation_request_update_cancelled_email(
    variation_request: VariationRequest, application: ImpOrExp
) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        VariationRequestUpdateCancelledEmail(
            application=application, variation_request=variation_request, to=[recipient]
        ).send()


def send_variation_request_update_received_email(
    variation_request: VariationRequest, application: ImpOrExp
) -> None:
    recipients = get_email_addresses_for_users([application.case_owner])
    for recipient in recipients:
        VariationRequestUpdateReceivedEmail(
            application=application, variation_request=variation_request, to=[recipient]
        ).send()


def send_variation_request_refused_email(
    variation_request: VariationRequest, application: ImpOrExp
):
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        VariationRequestRefusedEmail(
            application=application, variation_request=variation_request, to=[recipient]
        ).send()


def send_withdrawal_opened_email(withdrawal: WithdrawApplication) -> None:
    application = withdrawal.export_application or withdrawal.import_application
    recipients = get_case_officers_email_addresses(application.process_type)
    for recipient in recipients:
        WithdrawalOpenedEmail(withdrawal=withdrawal, to=[recipient]).send()


def send_withdrawal_accepted_email(withdrawal: WithdrawApplication) -> None:
    application = withdrawal.export_application or withdrawal.import_application
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        WithdrawalAcceptedEmail(withdrawal=withdrawal, to=[recipient]).send()


def send_withdrawal_cancelled_email(withdrawal: WithdrawApplication) -> None:
    application = withdrawal.export_application or withdrawal.import_application
    recipients = get_case_officers_email_addresses(application)
    for recipient in recipients:
        WithdrawalCancelledEmail(withdrawal=withdrawal, to=[recipient]).send()


def send_withdrawal_rejected_email(withdrawal: WithdrawApplication) -> None:
    application = withdrawal.export_application or withdrawal.import_application
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        WithdrawalRejectedEmail(withdrawal=withdrawal, to=[recipient]).send()


def send_application_reassigned_email(application: ImpOrExp, comment: str) -> None:
    recipients = get_email_addresses_for_users([application.case_owner])
    for recipient in recipients:
        ApplicationReassignedEmail(application=application, comment=comment, to=[recipient]).send()


def send_application_reopened_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationReopenedEmail(application=application, to=[recipient]).send()


def send_application_update_response_email(application: ImpOrExp) -> None:
    recipients = get_email_addresses_for_users([application.case_owner])
    for recipient in recipients:
        ApplicationUpdateResponseEmail(application=application, to=[recipient]).send()


def send_application_update_email(update_request: UpdateRequest) -> None:
    application = (
        update_request.importapplication_set.first() or update_request.exportapplication_set.first()
    )
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationUpdateEmail(
            application=application, update_request=update_request, to=[recipient]
        ).send()


def send_firearms_supplementary_report_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        FirearmsSupplementaryReportEmail(application=application, to=[recipient]).send()


def send_further_information_request_email(fir: FurtherInformationRequest):
    application = fir.exportapplication_set.first() or fir.importapplication_set.first()
    access_request = fir.accessrequest_set.first()
    if application:
        send_application_further_information_request_email(fir, application)
    elif access_request:
        send_access_request_further_information_request_email(fir, access_request)


def send_further_information_request_responded_email(fir: FurtherInformationRequest):
    application = fir.exportapplication_set.first() or fir.importapplication_set.first()
    access_request = fir.accessrequest_set.first()
    if application:
        send_application_further_information_request_responded_email(fir, application)
    elif access_request:
        send_access_request_further_information_request_responded_email(fir, access_request)


def send_further_information_request_withdrawn_email(fir: FurtherInformationRequest):
    application = fir.exportapplication_set.first() or fir.importapplication_set.first()
    access_request = fir.accessrequest_set.first()
    if application:
        send_application_further_information_request_withdrawn_email(fir, application)
    elif access_request:
        send_access_request_further_information_request_withdrawn_email(fir, access_request)


def send_access_request_further_information_request_responded_email(
    fir: FurtherInformationRequest, access_request: ImpAccessOrExpAccess
) -> None:
    # TODO: ICMSLST-2333 Gov Notify - Email attachments
    recipients = get_email_addresses_for_users([fir.requested_by])
    for recipient in recipients:
        AccessRequestFurtherInformationRequestRespondedEmail(
            fir=fir, access_request=access_request, to=[recipient]
        ).send()


def send_application_further_information_request_responded_email(
    fir: FurtherInformationRequest, application: ImpOrExp
) -> None:
    # TODO: ICMSLST-2333 Gov Notify - Email attachments
    application = application.get_specific_model()
    recipients = get_email_addresses_for_users([fir.requested_by])
    for recipient in recipients:
        ApplicationFurtherInformationRequestRespondedEmail(
            fir=fir, application=application, to=[recipient]
        ).send()


def send_access_request_further_information_request_withdrawn_email(
    fir: FurtherInformationRequest, access_request: ImpAccessOrExpAccess
) -> None:
    # TODO: ICMSLST-2333 Gov Notify - Email attachments
    recipients = get_email_addresses_for_users([access_request.submitted_by])
    for recipient in recipients:
        AccessRequestFurtherInformationRequestWithdrawnEmail(
            fir=fir, access_request=access_request, to=[recipient]
        ).send()


def send_application_further_information_request_withdrawn_email(
    fir: FurtherInformationRequest, application: ImpOrExp
) -> None:
    # TODO: ICMSLST-2333 Gov Notify - Email attachments
    application = application.get_specific_model()
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationFurtherInformationRequestWithdrawnEmail(
            fir=fir, application=application, to=[recipient]
        ).send()


def send_access_request_further_information_request_email(
    fir: FurtherInformationRequest, access_request: ImpAccessOrExpAccess
) -> None:
    # TODO: ICMSLST-2333 Gov Notify - Email attachments
    recipients = get_email_addresses_for_users([access_request.submitted_by])
    for recipient in recipients:
        AccessRequestFurtherInformationRequestEmail(
            fir=fir, access_request=access_request, to=[recipient]
        ).send()


def send_application_further_information_request_email(
    fir: FurtherInformationRequest, application: ImpOrExp
) -> None:
    # TODO: ICMSLST-2333 Gov Notify - Email attachments
    application = application.get_specific_model()
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        ApplicationFurtherInformationRequestEmail(
            fir=fir, application=application, to=[recipient]
        ).send()


def send_case_email(case_email: CaseEmailModel) -> None:
    # TODO: ICMSLST-2333 Gov Notify - Email attachments
    recipients = get_email_addresses_for_case_email(case_email)
    for recipient in recipients:
        CaseEmail(case_email=case_email, to=[recipient]).send()
    case_email.status = CaseEmailModel.Status.OPEN
    case_email.sent_datetime = timezone.now()
    case_email.save()


def create_case_email(
    application: ImpOrExp,
    template_code: CaseEmailTemplate,
    to: str | None = None,
    cc: list[str] | None = None,
    attachments: QuerySet | None = None,
) -> CaseEmail:
    subject, body = get_email_template_subject_body(application, template_code)

    case_email = CaseEmailModel.objects.create(
        subject=subject, body=body, to=to, cc_address_list=cc, template_code=template_code
    )

    if attachments:
        case_email.attachments.add(*attachments)

    return case_email


def send_licence_revoked_email(application: ImportApplication) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        LicenceRevokedEmail(application=application, to=[recipient]).send()


def send_certificate_revoked_email(application: ExportApplication) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        CertificateRevokedEmail(application=application, to=[recipient]).send()
