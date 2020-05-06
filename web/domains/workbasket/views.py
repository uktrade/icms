import structlog as logging
from django.views.generic.list import ListView

from web.auth.mixins import RequireRegisteredMixin
from web.domains.case.access.flows import AccessRequestFlow

from viewflow.models import Process

logger = logging.get_logger(__name__)


class Workbasket(RequireRegisteredMixin, ListView):
    template_name = 'web/domains/workbasket/workbasket.html'
    permission_required = []

    def get_queryset(self):
        return Process.objects.filter_available([AccessRequestFlow],
                                                self.request.user)
