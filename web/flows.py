import structlog as logging

from viewflow import flow, frontend
from viewflow.base import Flow, this
from web.domains import User
from web.domains.case.access.models import AccessRequest, AccessRequestProcess
from web.domains.case.access.views import (AccessRequestCreateView,
                                           ILBReviewRequest)
from web.notify import notify

# Get an instance of a logger
logger = logging.getLogger(__name__)


def send_admin_notification_email(activation):
    ilb_admins = User.objects.filter(is_staff=True)
    for admin in ilb_admins:
        try:
            notify.access_request_admin(admin,
                                        activation.process.access_request)
        except Exception as e:  # noqa
            logger.exception('Failed to notify an ILB admin', e)


def send_requester_notification_email(activation):
    notify.access_request_requester(activation.process.access_request)


def close_request(activation):
    activation.process.access_request.status = AccessRequest.CLOSED
    activation.process.access_request.save()


@frontend.register
class AccessRequestFlow(Flow):
    process_class = AccessRequestProcess

    start = (flow.Start(AccessRequestCreateView, ).Permission(
        'web.create_access_request').Next(this.email_admins))

    email_admins = (flow.Handler(send_admin_notification_email).Next(
        this.review_request))

    review_request = (flow.View(
        ILBReviewRequest, ).Permission('web.review_access_request').Next(
            this.email_requester))

    email_requester = (flow.Handler(send_requester_notification_email).Next(
        this.close_request))

    close_request = (flow.Handler(close_request).Next(this.end))

    end = flow.End()
