import structlog as logging
from django.views.generic.list import ListView
from viewflow.models import Process

from web.auth.mixins import RequireRegisteredMixin
from web.domains.case.access.approval.flows import ApprovalRequestFlow
from web.domains.case.access.flows import ExporterAccessRequestFlow, ImporterAccessRequestFlow
from web.domains.case.fir.flows import FurtherInformationRequestFlow

logger = logging.get_logger(__name__)


class Workbasket(RequireRegisteredMixin, ListView):
    template_name = "web/domains/workbasket/workbasket.html"
    permission_required = []

    def get_queryset(self):
        return Process.objects.filter_available(
            [
                ImporterAccessRequestFlow,
                ExporterAccessRequestFlow,
                ApprovalRequestFlow,
                FurtherInformationRequestFlow,
            ],
            self.request.user,
        )
