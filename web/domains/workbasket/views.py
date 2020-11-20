from itertools import chain

import structlog as logging
from django.db.models import Prefetch
from django.views.generic.list import ListView

from web.auth.mixins import RequireRegisteredMixin

from web.flow.models import Task
from web.domains.case.access.models import (
    AccessRequest,
    ExporterAccessRequest,
    ImporterAccessRequest,
)
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

        processes = []

        if self.request.user.has_perm("web.reference_data_access"):
            certificates = CertificateOfManufactureApplication.objects.filter(
                is_active=True
            ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
            exporter_access_requests = ExporterAccessRequest.objects.filter(
                is_active=True, status=AccessRequest.SUBMITTED
            ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
            importer_access_requests = ImporterAccessRequest.objects.filter(
                is_active=True, status=AccessRequest.SUBMITTED
            ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
            processes.extend([certificates, exporter_access_requests, importer_access_requests])

        processes.append(
            self.request.user.submitted_access_requests.filter(status=AccessRequest.SUBMITTED)
            .prefetch_related("further_information_requests")
            .prefetch_related(
                Prefetch(
                    "further_information_requests__tasks",
                    queryset=Task.objects.filter(is_active=True, owner=self.request.user),
                )
            )
        )

        return chain(*processes)
