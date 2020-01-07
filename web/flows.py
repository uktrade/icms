from viewflow import flow, frontend
from viewflow.base import this, Flow

from web.domains.case.access.models import AccessRequestProcess
from web.domains.case.access.views import (
    AccessRequestCreateView,
    AccessRequestCreatedView
)


@frontend.register
class AccessRequestFlow(Flow):
    process_class = AccessRequestProcess

    start = (
        flow.Start(
            AccessRequestCreateView,
        ).Permission(
            auto_create=True
        ).Next(this.review_request)
    )

    review_request = (
        flow.View(
            AccessRequestCreatedView,
        ).Permission(
            auto_create=True
        ).Next(this.end)
    )

    end = flow.End()


