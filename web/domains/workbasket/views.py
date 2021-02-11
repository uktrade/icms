from itertools import chain

import structlog as logging
from django.db.models import Prefetch
from django.views.generic.list import ListView
from guardian.shortcuts import get_objects_for_user

from web.auth.mixins import RequireRegisteredMixin
from web.domains.case._import.firearms.models import (
    ImportApplication,
    OpenIndividualLicenceApplication,
)
from web.domains.case.access.approval.models import (
    ExporterApprovalRequest,
    ImporterApprovalRequest,
)
from web.domains.case.access.models import (
    AccessRequest,
    ExporterAccessRequest,
    ImporterAccessRequest,
)
from web.domains.case.export.models import CertificateOfManufactureApplication
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.flow.models import Task

logger = logging.get_logger(__name__)


class Workbasket(RequireRegisteredMixin, ListView):
    template_name = "web/domains/workbasket/workbasket.html"
    permission_required = []

    def get_queryset(self):
        if self.request.user.has_perm("web.reference_data_access"):
            return self.get_queryset_admin()
        else:
            return self.get_queryset_user()

    def get_queryset_admin(self):
        certificates = CertificateOfManufactureApplication.objects.filter(
            is_active=True
        ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

        exporter_access_requests = ExporterAccessRequest.objects.filter(
            is_active=True, status=AccessRequest.SUBMITTED
        ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

        importer_access_requests = ImporterAccessRequest.objects.filter(
            is_active=True, status=AccessRequest.SUBMITTED
        ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

        oil_import_application = OpenIndividualLicenceApplication.objects.filter(
            is_active=True
        ).prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))

        return chain(
            certificates, exporter_access_requests, importer_access_requests, oil_import_application
        )

    def get_queryset_user(self):
        # current user's exporters
        # TODO: check if agent's contacts can do Approval Request
        exporters = get_objects_for_user(self.request.user, ["is_contact_of_exporter"], Exporter)

        # current user's importers
        # TODO: check if agent's contacts can do Approval Request
        importers = get_objects_for_user(self.request.user, ["is_contact_of_importer"], Importer)

        exporter_approval_requests = (
            ExporterApprovalRequest.objects.select_related(
                # get the exporter associated with the approval request
                # join access_request and join exporter from access_request
                "access_request__exporteraccessrequest__link",
            )
            .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
            .filter(is_active=True)
            .filter(access_request__exporteraccessrequest__link__in=exporters)
        )

        importer_approval_requests = (
            ImporterApprovalRequest.objects.select_related(
                # get the importer associated with the approval request
                # join access_request and join importer from access_request
                "access_request__importeraccessrequest__link",
            )
            .prefetch_related(Prefetch("tasks", queryset=Task.objects.filter(is_active=True)))
            .filter(is_active=True)
            .filter(access_request__importeraccessrequest__link__in=importers)
        )

        # user/admin access requests and firs
        access_requests = (
            self.request.user.submitted_access_requests.filter(status=AccessRequest.SUBMITTED)
            .prefetch_related("further_information_requests")
            .prefetch_related(
                Prefetch(
                    "further_information_requests__tasks",
                    queryset=Task.objects.filter(is_active=True, owner=self.request.user),
                )
            )
        )

        # Import Application - Open Individual Licence (OIL)
        oil_import_application = (
            OpenIndividualLicenceApplication.objects.prefetch_related(
                Prefetch("tasks", queryset=Task.objects.filter(is_active=True))
            )
            .filter(is_active=True)
            .filter(
                status__in=[
                    ImportApplication.SUBMITTED,
                    ImportApplication.IN_PROGRESS,
                    ImportApplication.WITHDRAWN,
                ]
            )
            .filter(importer__in=importers)
        )

        return chain(
            exporter_approval_requests,
            importer_approval_requests,
            access_requests,
            oil_import_application,
        )
