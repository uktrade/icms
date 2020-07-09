import structlog as logging
from django.views.generic.list import ListView

from web.auth.mixins import RequireRegisteredMixin
from web.domains.case.access.flows import ImporterAccessRequestFlow, ExporterAccessRequestFlow
from web.domains.case.access.approval.flows import ApprovalRequestFlow

from viewflow.models import Process

logger = logging.get_logger(__name__)


class Workbasket(RequireRegisteredMixin, ListView):
    template_name = "web/domains/workbasket/workbasket.html"
    permission_required = []

    def get_queryset(self):
        return Process.objects.filter_available(
            [ImporterAccessRequestFlow, ExporterAccessRequestFlow, ApprovalRequestFlow],
            self.request.user,
        )
