from viewflow import flow, frontend
from viewflow.base import this, Flow

from web.domains.case.access.models import AccessRequestProcess, AccessRequest
from web.domains.case.access.views import (
    AccessRequestCreateView,
    ILBReviewRequest,
)


def send_admin_notification_email(activation):
    print(f'Request from {activation.process.access_request.organisation_name}')  # TODO


def send_requester_notification_email(activation):
    print(f'{activation.process.access_request.organisation_name}: {activation.process.access_request.response}')  # TODO


def close_request(activation):
    activation.process.access_request.status = AccessRequest.CLOSED
    activation.process.access_request.save()


@frontend.register
class AccessRequestFlow(Flow):
    process_class = AccessRequestProcess

    start = (
        flow.Start(
            AccessRequestCreateView,
        ).Permission(
            'web.create_access_request'
        ).Next(this.email_admins)
    )

    email_admins = (
        flow.Handler(
            send_admin_notification_email
        ).Next(this.review_request)
    )

    review_request = (
        flow.View(
            ILBReviewRequest,
        ).Permission(
            'web.review_access_request'
        ).Next(this.email_requester)
    )

    email_requester = (
        flow.Handler(
            send_requester_notification_email
        ).Next(this.close_request)
    )

    close_request = (
        flow.Handler(
            close_request
        ).Next(this.end)
    )

    end = flow.End()
