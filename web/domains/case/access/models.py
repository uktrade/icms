import structlog as logging
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.user.models import User
from web.domains.workbasket.base import WorkbasketAction, WorkbasketBase, WorkbasketRow
from web.flow.models import Process

logger = logging.getLogger(__name__)


class AccessRequest(WorkbasketBase, Process):
    APPROVED = "APPROVED"
    REFUSED = "REFUSED"
    RESPONSES = ((APPROVED, "Approved"), (REFUSED, "Refused"))

    # TODO: ICMSLST-634 see if we can remove the type:ignores once we have django-stubs
    class Statuses(models.TextChoices):
        SUBMITTED: str = ("SUBMITTED", "Submitted")  # type:ignore[assignment]
        CLOSED: str = ("CLOSED", "Closed")  # type:ignore[assignment]

    reference = models.CharField(max_length=100, blank=False, null=False, unique=True)

    status = models.CharField(
        max_length=30, choices=Statuses.choices, blank=False, null=False, default=Statuses.SUBMITTED
    )

    organisation_name = models.CharField(max_length=100, blank=False, null=False)
    organisation_address = models.TextField()
    organisation_registered_number = models.CharField(
        max_length=100, blank=True, default="", verbose_name="Registered Number"
    )
    request_reason = models.TextField(
        verbose_name="What are you importing and where are you importing it from?"
    )
    agent_name = models.CharField(max_length=100, blank=True, null=True)
    agent_address = models.TextField(blank=True, default="")

    submit_datetime = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="submitted_access_requests",
    )
    last_update_datetime = models.DateTimeField(auto_now=True, blank=False, null=False)
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="updated_access_requests",
    )
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="closed_access_requests"
    )
    response = models.CharField(max_length=20, choices=RESPONSES, blank=False, null=True)
    response_reason = models.TextField(blank=True, default="")

    further_information_requests = models.ManyToManyField(FurtherInformationRequest)

    @cached_property
    def submitted_by_email(self):
        if self.submitted_by:
            return self.submitted_by.email
        return None

    def get_workbasket_row(self, user: User) -> WorkbasketRow:
        r = WorkbasketRow()

        r.reference = self.reference

        r.subject = self.process_type

        r.company = "\n".join(
            [
                f"{self.submitted_by} {self.submitted_by.email}",
                self.organisation_name,
                self.organisation_address,
            ]
        )

        r.status = self.get_status_display()

        r.timestamp = self.created

        info_rows = ["Access Request"]

        if self.further_information_requests.open():
            info_rows.append("Further Information Requested")

        if self.approval_requests.filter(is_active=True) and user.has_perm(
            "web.reference_data_access"
        ):
            info_rows.append("Approval Requested")

        r.information = "\n".join(info_rows)

        task = self.get_active_task()

        if user.has_perm("web.reference_data_access"):
            admin_actions: list[WorkbasketAction] = []

            if self.process_type == "ExporterAccessRequest":
                entity = "exporter"
            elif self.process_type == "ImporterAccessRequest":
                entity = "importer"
            else:
                raise NotImplementedError(f"process_type: {self.process_type} not supported")

            admin_actions.append(
                WorkbasketAction(
                    is_post=False,
                    name="Manage",
                    url=reverse("access:case-management", kwargs={"pk": self.pk, "entity": entity}),
                ),
            )

            r.actions.append(admin_actions)

        if task and task.owner == user:
            owner_actions: list[WorkbasketAction] = [
                WorkbasketAction(
                    is_post=False,
                    name="View",
                    url=reverse(
                        "case:view", kwargs={"application_pk": self.pk, "case_type": "access"}
                    ),
                )
            ]

            for fir in self.further_information_requests.open():
                kwargs = {"application_pk": self.pk, "fir_pk": fir.pk, "case_type": "access"}

                owner_actions.append(
                    WorkbasketAction(
                        is_post=False,
                        name="Respond FIR",
                        url=reverse("case:respond-fir", kwargs=kwargs),
                    ),
                )

            r.actions.append(owner_actions)

        return r


class ImporterAccessRequest(AccessRequest):
    PROCESS_TYPE = "ImporterAccessRequest"

    AGENT_ACCESS = "AGENT_IMPORTER_ACCESS"
    REQUEST_TYPES = (
        ("MAIN_IMPORTER_ACCESS", "Request access to act as an Importer"),
        (AGENT_ACCESS, "Request access to act as an Agent for an Importer"),
    )
    eori_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="EORI Number",
        help_text="EORI number should include the GB prefix for organisation or GBPR for individual",
    )
    eori_number_ni = models.CharField(
        max_length=20, blank=True, default="", verbose_name="NI EORI Number"
    )

    link = models.ForeignKey(
        Importer, on_delete=models.PROTECT, blank=True, null=True, related_name="access_requests"
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPES, verbose_name="Access Request Type"
    )


class ExporterAccessRequest(AccessRequest):
    PROCESS_TYPE = "ExporterAccessRequest"

    AGENT_ACCESS = "AGENT_EXPORTER_ACCESS"
    REQUEST_TYPES = (
        ("MAIN_EXPORTER_ACCESS", "Request access to act as an Exporter"),
        (AGENT_ACCESS, "Request access to act as an Agent for an Exporter"),
    )

    link = models.ForeignKey(
        Exporter, on_delete=models.PROTECT, blank=True, null=True, related_name="access_requests"
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPES, verbose_name="Access Request Type"
    )
