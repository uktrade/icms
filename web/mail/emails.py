from web.domains.case.types import ImpAccessOrExpAccess, ImpOrExp
from web.flow.models import ProcessTypes
from web.models import VariationRequest
from web.notify import notify

from .messages import (
    AccessRequestClosedEmail,
    AccessRequestEmail,
    ApplicationCompleteEmail,
    ApplicationExtensionCompleteEmail,
    ApplicationStoppedEmail,
    ApplicationVariationCompleteEmail,
)
from .recipients import (
    get_application_contact_email_addresses,
    get_email_addresses_for_users,
    get_ilb_case_officers_email_addresses,
)


def send_access_requested_email(access_request: ImpAccessOrExpAccess) -> None:
    recipients = get_ilb_case_officers_email_addresses()
    for recipient in recipients:
        email = AccessRequestEmail(access_request=access_request, to=[recipient])
        email.send()


def send_access_request_closed_email(access_request: ImpAccessOrExpAccess) -> None:
    recipients = get_email_addresses_for_users([access_request.submitted_by])
    for recipient in recipients:
        email = AccessRequestClosedEmail(access_request=access_request, to=[recipient])
        email.send()


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
        email = ApplicationExtensionCompleteEmail(application=application, to=[recipient])
        email.send()


def send_application_variation_complete_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        email = ApplicationVariationCompleteEmail(application=application, to=[recipient])
        email.send()


def send_application_complete_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        email = ApplicationCompleteEmail(application=application, to=[recipient])
        email.send()


def send_completed_application_process_notifications(application: ImpOrExp) -> None:
    if application.process_type == ProcessTypes.FA_DFL:
        # TODO: ICMSLST-2145 Update to use GOV Notify
        notify.send_constabulary_deactivated_firearms_notification(application.dflapplication)

    if application.process_type in [ProcessTypes.FA_DFL, ProcessTypes.FA_OIL, ProcessTypes.FA_SIL]:
        # TODO: ICMSLST-2153 Update to use GOV Notify
        notify.send_supplementary_report_notification(application)

    send_completed_application_email(application)


def send_application_stopped_email(application: ImpOrExp) -> None:
    recipients = get_application_contact_email_addresses(application)
    for recipient in recipients:
        email = ApplicationStoppedEmail(application=application, to=[recipient])
        email.send()
