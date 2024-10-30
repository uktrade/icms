from django.conf import settings
from django.db import models
from django.utils import timezone

from web.types import TypedTextChoices


class ProcessTypes(TypedTextChoices):
    """Values for Process.process_type."""

    # import
    DEROGATIONS = ("DerogationsApplication", "Derogation from Sanctions Import Ban")
    FA_DFL = ("DFLApplication", "Firearms and Ammunition (Deactivated Firearms Licence)")
    FA_OIL = (
        "OpenIndividualLicenceApplication",
        "Firearms and Ammunition (Open Individual Import Licence)",
    )
    FA_SIL = ("SILApplication", "Firearms and Ammunition (Specific Individual Import Licence)")
    OPT = ("OutwardProcessingTradeApplication", "Outward Processing Trade")
    SANCTIONS = ("SanctionsAndAdhocApplication", "Sanctions and Adhoc Licence Application")
    SPS = ("PriorSurveillanceApplication", "Prior Surveillance")
    TEXTILES = ("TextilesApplication", "Textiles (Quota)")
    WOOD = ("WoodQuotaApplication", "Wood (Quota)")

    # export
    COM = ("CertificateOfManufactureApplication", "Certificate of Manufacture")
    CFS = ("CertificateOfFreeSaleApplication", "Certificate of Free Sale")
    GMP = (
        "CertificateofGoodManufacturingPractice",
        "Certificate of Good Manufacturing Practice",
    )

    # Import and Export FIR
    FIR = ("FurtherInformationRequest", "Further Information Requests")

    # Access requests
    IAR = ("ImporterAccessRequest", "Importer Access Request")
    EAR = ("ExporterAccessRequest", "Exporter Access Request")

    # Approval requests
    ExpApprovalReq = ("ExporterApprovalRequest", "Exporter Approval Request")
    ImpApprovalReq = ("ImporterApprovalRequest", "Importer Approval Request")


class Process(models.Model):
    """Base class for all processes."""

    # each final subclass needs to set this for downcasting to work; see
    # get_specific_model. they should also mark themselves with typing.final.
    IS_FINAL = False

    # the default=None is to force all code to set this when creating objects.
    # it will fail when save is called.
    process_type = models.CharField(max_length=50, default=None)

    is_active = models.BooleanField(default=True, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)

    # Used to order the workbasket - Changes when a variety of actions are performed
    order_datetime = models.DateTimeField(default=timezone.now)

    def get_application_details_link(self) -> str:
        """Used in applicant views when creating an application.

        Places used:
            - web/templates/partial/case/sidebar.html
        """

        pt = ProcessTypes
        match self.process_type:
            case pt.FA_DFL | pt.FA_OIL | pt.FA_SIL:
                return "Firearms and Ammunition"
            case pt.TEXTILES:
                return "Textiles"
            case pt.WOOD:
                return "Wood"
            case pt.DEROGATIONS:
                return "Sanctions Derogation"
            case pt.SPS:
                return "Prior Surveillance"
            case pt.SANCTIONS:
                return "Sanctions and Adhoc"
            case pt.OPT:
                return "Outward Processing Trade"
            # Export
            case pt.CFS:
                return "CFS Application"
            case pt.COM:
                return "COM Application"
            case pt.GMP:
                return "GMP Application"
            case _:
                # Return the old default if we have missed any / add more.
                return "Application Details"

    def get_specific_model(self) -> "Process":
        """Downcast to specific model class."""

        # if we already have the specific model, just return it
        if self.IS_FINAL:
            return self

        pt = self.process_type

        # importer/exporter access requests
        if pt == ProcessTypes.IAR:
            return self.accessrequest.importeraccessrequest

        elif pt == ProcessTypes.EAR:
            return self.accessrequest.exporteraccessrequest

        # import applications
        elif pt == ProcessTypes.FA_OIL:
            return self.importapplication.openindividuallicenceapplication

        elif pt == ProcessTypes.FA_SIL:
            return self.importapplication.silapplication

        elif pt == ProcessTypes.SANCTIONS:
            return self.importapplication.sanctionsandadhocapplication

        elif pt == ProcessTypes.WOOD:
            return self.importapplication.woodquotaapplication

        elif pt == ProcessTypes.DEROGATIONS:
            return self.importapplication.derogationsapplication

        elif pt == ProcessTypes.FA_DFL:
            return self.importapplication.dflapplication

        elif pt == ProcessTypes.OPT:
            return self.importapplication.outwardprocessingtradeapplication

        elif pt == ProcessTypes.TEXTILES:
            return self.importapplication.textilesapplication

        elif pt == ProcessTypes.SPS:
            return self.importapplication.priorsurveillanceapplication

        # Export applications
        elif pt == ProcessTypes.COM:
            return self.exportapplication.certificateofmanufactureapplication

        elif pt == ProcessTypes.CFS:
            return self.exportapplication.certificateoffreesaleapplication

        elif pt == ProcessTypes.GMP:
            return self.exportapplication.certificateofgoodmanufacturingpracticeapplication

        else:
            raise NotImplementedError(f"Unknown process_type {pt}")

    def update_order_datetime(self) -> None:
        self.order_datetime = timezone.now()


class Task(models.Model):
    """A task. A process can have as many tasks as it wants attached to it, and
    tasks maintain a "previous" link to track the task ordering.

    NOTE: a task can have multiple child tasks, but only one parent task.
    """

    class TaskType(TypedTextChoices):
        PREPARE: str = ("prepare", "Prepare")  # type:ignore[assignment]
        PROCESS: str = ("process", "Process")  # type:ignore[assignment]
        VR_REQUEST_CHANGE: str = (
            "vr_request_change",
            "VR_REQUEST_CHANGE",
        )  # type:ignore[assignment]
        AUTHORISE: str = ("authorise", "Authorise")  # type:ignore[assignment]

        DOCUMENT_ERROR: str = ("document_error", "Digital signing error")  # type:ignore[assignment]
        DOCUMENT_SIGNING: str = ("document_signing", "Digital signing")  # type:ignore[assignment]

        CHIEF_WAIT: str = ("chief_wait", "CHIEF_WAIT")  # type:ignore[assignment]
        CHIEF_REVOKE_WAIT: str = (
            "chief_revoke_wait",
            "CHIEF_REVOKE_WAIT",
        )  # type:ignore[assignment]
        CHIEF_ERROR: str = ("chief_error", "CHIEF_ERROR")  # type:ignore[assignment]

        REJECTED: str = ("rejected", "Rejected")  # type:ignore[assignment]

    process = models.ForeignKey("web.Process", on_delete=models.CASCADE, related_name="tasks")

    task_type = models.CharField(max_length=30, choices=TaskType.choices)

    is_active = models.BooleanField(default=True, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)

    previous = models.ForeignKey("self", related_name="next", null=True, on_delete=models.CASCADE)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        on_delete=models.CASCADE,
        related_name="+",
    )

    def __str__(self):
        return f"Task(pk={self.id!r}, task_type={self.task_type!r})"
