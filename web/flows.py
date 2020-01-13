from viewflow import flow, frontend
from viewflow.base import this, Flow

from web.domains.case.access.models import AccessRequestProcess, AccessRequest
from web.domains.case.access.views import (
    AccessRequestCreateView,
    ILBReviewRequest,
    AccessRefused,
    AccessApproved
)


@frontend.register
class AccessRequestFlow(Flow):
    process_class = AccessRequestProcess

    start = (
        flow.Start(
            AccessRequestCreateView,
        ).Permission(
            'web.create_access_request'
        ).Next(this.review_request)
    )

    review_request = (
        flow.View(
            ILBReviewRequest,
        ).Permission(
            'web.review_access_request'
        ).Next(this.check_response)
    )

    check_response = flow.If(
        cond=lambda act: act.process.access_request.response == AccessRequest.APPROVED
    ).Then(
        this.approved_access_request
    ).Else(
        this.refused_access_request
    )

    approved_access_request = flow.View(
        AccessApproved,
    ).Assign(
        this.review_request.owner
    ).Permission(
        'web.review_access_request'
    ).Next(this.end)

    refused_access_request = flow.View(
        AccessRefused,
    ).Assign(
        this.review_request.owner
    ).Permission(
        'web.review_access_request'
    ).Next(this.end)

    end = flow.End()
