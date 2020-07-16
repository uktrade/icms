import structlog as logging
from django.db.models import Prefetch
from django.views.generic.list import ListView

from web.auth.mixins import RequireRegisteredMixin

from web.flow.models import Task
from web.domains.case.export.models import CertificateOfManufactureApplication

logger = logging.get_logger(__name__)


class Workbasket(RequireRegisteredMixin, ListView):
    template_name = "web/domains/workbasket/workbasket.html"
    permission_required = []

    def get_queryset(self):
        # TODO: remove once converted
        # return Process.objects.filter_available(
        #     [
        #         ImporterAccessRequestFlow,
        #         ExporterAccessRequestFlow,
        #         ApprovalRequestFlow,
        #         FurtherInformationRequestFlow,
        #     ],
        #     self.request.user,
        # )

        # TODO: implement below
        #   * change to django-guardian
        #   * if admin/case officer, filter by all
        #   * if external user, filter by "all exporters i have access to"

        return CertificateOfManufactureApplication.objects.filter(is_active=True).prefetch_related(
            Prefetch("tasks", queryset=Task.objects.filter(is_active=True))
        )
