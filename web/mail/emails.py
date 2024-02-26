import datetime as dt

from django.contrib.sites.models import Site
from django.db.models import QuerySet
from django.utils import timezone

from web.domains.case.types import (
    Authority,
    ImpAccessOrExpAccess,
    ImpOrExp,
    ImpOrExpApproval,
    Organisation,
)
from web.domains.template.utils import get_email_template_subject_body
from web.flow.models import ProcessTypes
from web.models import CaseEmail as CaseEmailModel
from web.models import (
    Constabulary,
    DFLApplication,
    ExportApplication,
    Exporter,
    ExporterApprovalRequest,
    ExporterContactInvite,
    FirearmsAuthority,
    FurtherInformationRequest,
    ImportApplication,
    Importer,
    ImporterApprovalRequest,
    ImporterContactInvite,
    Mailshot,
    Section5Authority,
    UpdateRequest,
    User,
    VariationRequest,
    WithdrawApplication,
)
from web.sites import get_exporter_site_domain, get_importer_site_domain

from .constants import EmailTypes
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
    AuthorityArchivedEmail,
    CaseEmail,
    CertificateRevokedEmail,
    ConstabularyDeactivatedFirearmsEmail,
    ExporterAccessRequestApprovalOpenedEmail,
    FirearmsAuthorityExpiringEmail,
    FirearmsSupplementaryReportEmail,
    ImporterAccessRequestApprovalOpenedEmail,
    LicenceRevokedEmail,
    MailshotEmail,
    NewUserWelcomeEmail,
    OrganisationContactInviteEmail,
    RetractMailshotEmail,
    Section5AuthorityExpiringEmail,
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
    get_email_addresses_for_constabulary,
    get_email_addresses_for_mailshot,
    get_email_addresses_for_section_5_expiring_authorities,
    get_email_addresses_for_users,
    get_ilb_case_officers_email_addresses,
    get_organisation_contact_email_addresses,
    get_shared_mailbox_for_constabulary,
)
from .types import ImporterDetails


def send_new_user_welcome_email(user: User, site: Site) -> None:
    NewUserWelcomeEmail(user=user, site=site, to=[user.email]).send()


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
        send_constabulary_deactivated_firearms_email(application.dflapplication)

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
    email_type: EmailTypes,
    application: ImpOrExp,
) -> None:
    match email_type:
        case EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED:
            send_variation_request_cancelled_email(variation_request, application)
        case EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED:
            send_variation_request_update_required_email(variation_request, application)
        case EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED:
            send_variation_request_update_cancelled_email(variation_request, application)
        case EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED:
            send_variation_request_update_received_email(variation_request, application)
        case EmailTypes.APPLICATION_VARIATION_REQUEST_REFUSED:
            send_variation_request_refused_email(variation_request, application)
        case _:
            raise ValueError("Unsupported Email Type %s for Variation Request" % email_type)


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
) -> None:
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


def send_further_information_request_email(fir: FurtherInformationRequest) -> None:
    application = fir.exportapplication_set.first() or fir.importapplication_set.first()
    access_request = fir.accessrequest_set.first()
    if application:
        send_application_further_information_request_email(fir, application)
    elif access_request:
        send_access_request_further_information_request_email(fir, access_request)


def send_further_information_request_responded_email(fir: FurtherInformationRequest) -> None:
    application = fir.exportapplication_set.first() or fir.importapplication_set.first()
    access_request = fir.accessrequest_set.first()
    if application:
        send_application_further_information_request_responded_email(fir, application)
    elif access_request:
        send_access_request_further_information_request_responded_email(fir, access_request)


def send_further_information_request_withdrawn_email(fir: FurtherInformationRequest) -> None:
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


def send_mailshot_email(mailshot: Mailshot) -> None:
    if mailshot.is_to_importers:
        send_mailshot_email_to_organisations(mailshot, Importer, get_importer_site_domain())
    if mailshot.is_to_exporters:
        send_mailshot_email_to_organisations(mailshot, Exporter, get_exporter_site_domain())


def send_mailshot_email_to_organisations(
    mailshot: Mailshot, organisation_class: type[Organisation], site_domain: str
) -> None:
    recipients = get_email_addresses_for_mailshot(organisation_class)
    for recipient in recipients:
        MailshotEmail(mailshot=mailshot, site_domain=site_domain, to=[recipient]).send()


def send_retract_mailshot_email(mailshot: Mailshot) -> None:
    if mailshot.is_to_importers:
        send_retract_mailshot_email_to_organisations(mailshot, Importer, get_importer_site_domain())
    if mailshot.is_to_exporters:
        send_retract_mailshot_email_to_organisations(mailshot, Exporter, get_exporter_site_domain())


def send_retract_mailshot_email_to_organisations(
    mailshot: Mailshot, organisation_class: type[Organisation], site_domain: str
) -> None:
    recipients = get_email_addresses_for_mailshot(organisation_class)
    for recipient in recipients:
        RetractMailshotEmail(mailshot=mailshot, site_domain=site_domain, to=[recipient]).send()


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
    email_type: EmailTypes,
    to: str | None = None,
    cc: list[str] | None = None,
    attachments: QuerySet | None = None,
) -> CaseEmail:
    template_code = email_type.value
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


def send_authority_archived_email(authority: Authority) -> None:
    recipients = get_ilb_case_officers_email_addresses()
    for recipient in recipients:
        AuthorityArchivedEmail(authority=authority, to=[recipient]).send()


def send_authority_expiring_section_5_email(
    importers_details: list[ImporterDetails], expiry_date: dt.date
) -> None:
    recipients = get_email_addresses_for_section_5_expiring_authorities()
    for recipient in recipients:
        Section5AuthorityExpiringEmail(
            importers_details=importers_details,
            authority_type=Section5Authority.AUTHORITY_TYPE,
            expiry_date=expiry_date,
            to=[recipient],
        ).send()


def send_authority_expiring_firearms_email(
    importers_details: list[ImporterDetails], expiry_date: dt.date, constabulary: Constabulary
) -> None:
    recipients = get_email_addresses_for_constabulary(constabulary)
    for recipient in recipients:
        FirearmsAuthorityExpiringEmail(
            importers_details=importers_details,
            authority_type=FirearmsAuthority.AUTHORITY_TYPE,
            expiry_date=expiry_date,
            constabulary=constabulary,
            to=[recipient],
        ).send()


def send_constabulary_deactivated_firearms_email(application: DFLApplication) -> None:
    recipient = get_shared_mailbox_for_constabulary(application.constabulary)
    ConstabularyDeactivatedFirearmsEmail(application=application, to=recipient).send()


def send_org_contact_invite_email(
    organisation: Importer | Exporter, invite: ImporterContactInvite | ExporterContactInvite
) -> None:
    OrganisationContactInviteEmail(
        organisation=organisation, invite=invite, to=[invite.email]
    ).send()
