from typing import List, Optional, Union

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet

from . import errors


class ProcessTypes(models.TextChoices):
    """Values for Process.process_type."""

    # import
    DEROGATIONS = ("DerogationsApplication", "Derogation from Sanctions Import Ban")
    FA_DFL = ("DFLApplication", "Firearms and Ammunition (Deactivated Firearms Licence)")
    FA_OIL = (
        "OpenIndividualLicenceApplication",
        "Firearms and Ammunition (Open Individual Import Licence)",
    )
    FA_SIL = ("SILApplication", "Firearms and Ammunition (Specific Individual Import Licence)")
    IRON_STEEL = ("ISQuotaApplication", "Iron and Steel (Quota)")
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

    # access requests
    IAR = ("ImporterAccessRequest", "Importer Access Request")
    EAR = ("ExporterAccessRequest", "Exporter Access Request")

    # TODO: FIRs and access request approvals also inherit from process, they
    # should probably be listed here as well


class Process(models.Model):
    """Base class for all processes."""

    # the default=None is to force all code to set this when creating objects.
    # it will fail when save is called.
    process_type = models.CharField(max_length=50, default=None)

    is_active = models.BooleanField(default=True, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)

    def get_task(self, expected_state: Union[str, List[str]], task_type: str) -> "Task":
        """Get the latest active task of the given type attached to this
        process, while also checking the process is in the expected state.

        NOTE: This locks the task row for update, so make sure there is an
        active transaction.

        NOTE: this function only makes sense if there is at most one active task
        of the type. If the process can have multiple active tasks of the same
        type, you cannot use this function.

        Raises an exception if anything goes wrong.
        """

        if not self.is_active:
            raise errors.ProcessInactiveError("Process is not active")

        # status is set as a model field on all derived classes
        status: str = self.status  # type: ignore[attr-defined]

        if isinstance(expected_state, list):
            if status not in expected_state:
                raise errors.ProcessStateError(f"Process is in the wrong state: {status}")
        else:
            if status != expected_state:
                raise errors.ProcessStateError(f"Process is in the wrong state: {status}")

        tasks = (
            self.tasks.filter(is_active=True, task_type=task_type)
            .order_by("created")
            .select_for_update()
        )

        if len(tasks) != 1:
            raise errors.TaskError(f"Expected one active task, got {len(tasks)}")

        return tasks[0]

    def get_active_tasks(self) -> "QuerySet[Task]":
        """Get all active task for current process.

        NOTE: This locks the tasks for update, so make sure there is an
        active transaction.

        Useful when soft deleting a process.
        """
        return self.tasks.filter(is_active=True).select_for_update()

    def get_active_task(self) -> "Optional[Task]":
        """Get the only active task attached to this process. If there is more
        than one active task, raises an error. If there is no active task,
        returns None."""

        tasks = self.tasks.filter(is_active=True)

        if len(tasks) == 1:
            return tasks[0]
        elif len(tasks) == 0:
            return None
        else:
            raise errors.TaskError(f"Expected one/zero active tasks, got {len(tasks)}")


class Task(models.Model):
    """A task. A process can have as many tasks as it wants attached to it, and
    tasks maintain a "previous" link to track the task ordering.

    NOTE: a task can have multiple child tasks, but only one parent task.
    """

    class TaskType(models.TextChoices):
        PREPARE: str = ("prepare", "Prepare")  # type:ignore[assignment]
        PROCESS: str = ("process", "Process")  # type:ignore[assignment]
        AUTHORISE: str = ("authorise", "Authorise")  # type:ignore[assignment]
        CHIEF_WAIT: str = ("chief_wait", "CHIEF_WAIT")  # type:ignore[assignment]
        CHIEF_ERROR: str = ("chief_error", "CHIEF_ERROR")  # type:ignore[assignment]
        ACK: str = ("acknowledge", "Acknowledge")  # type:ignore[assignment]

    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name="tasks")

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
        return f"{self.id}"
