from django.db.models import Q

from data_migration.models import Process
from web.models import Task


class TaskBase:
    TASK_TYPE: str = ""
    WB_ACTIONS: list[str] = []

    @classmethod
    def task_batch(cls) -> list[Task]:
        """Prepare Task objects to be created with bulk_create"""

        return [
            Task(**{"process_id": pk, "task_type": cls.TASK_TYPE}) for pk in cls.get_process_pks()
        ]

    @classmethod
    def get_process_pks(cls) -> list[int]:
        """Return a list of all process pks that require the TASK_TYPE"""

        pks = Process.objects.filter(
            Q(ima_workbasket__action_mnem__in=cls.WB_ACTIONS, ima_workbasket__is_active=True)
            | Q(ca_workbasket__action_mnem__in=cls.WB_ACTIONS, ca_workbasket__is_active=True)
        ).values_list("pk", flat=True)

        return pks


class PrepareTask(TaskBase):
    TASK_TYPE = Task.TaskType.PREPARE
    WB_ACTIONS = ["1.IMA2.IMP_IMA", "2.IMA2.IMP_IMA"]

    @classmethod
    def get_process_pks(cls) -> list[int]:
        # TODO: Extend to include other process children (e.g FIR)
        pks = Process.objects.filter(
            Q(importapplication__status="IN_PROGRESS") | Q(exportapplication__status="IN_PROGRESS")
        ).values_list("pk", flat=True)

        return pks


class ProcessTask(TaskBase):
    TASK_TYPE = Task.TaskType.PROCESS

    @classmethod
    def get_process_pks(cls) -> list[int]:
        # TODO: Extend to include other process children (e.g. FIR)
        # TODO: Refine to not overlap with other tasks (e.g authorise, chief_wait)
        pks = Process.objects.filter(
            Q(importapplication__status__in=["SUBMITTED", "PROCESSING"])
            | Q(exportapplication__status__in=["SUBMITTED", "PROCESSING"])
        ).values_list("pk", flat=True)

        return pks


class RejectedTask(TaskBase):
    TASK_TYPE = Task.TaskType.REJECTED

    @classmethod
    def get_process_pks(cls) -> list[int]:
        # V1 ImportApplication with decsion REFUSE are status COMPLETED, REVOKED, WITHDRAWN
        # V1 ExportApplication with decision REFUSED are status COMPLETED, STOPPED, WITHDRAWN

        pks = Process.objects.filter(
            Q(importapplication__decision="REFUSE") | Q(exportapplication__decision="REFUSE")
        ).values_list("pk", flat=True)

        return pks


class AuthTask(TaskBase):
    TASK_TYPE = Task.TaskType.AUTHORISE
    WB_ACTIONS = ["1.IMA4.IMP_IMA", "i.G2.AUTH_ISSUE", "10.CA110.IMP_CA"]


class VRRequestTask(TaskBase):
    TASK_TYPE = Task.TaskType.VR_REQUEST_CHANGE
    WB_ACTIONS = ["1.IMA25.IMP_IMA"]


class CHIEFWaitTask(TaskBase):
    TASK_TYPE = Task.TaskType.CHIEF_WAIT
    WB_ACTIONS = ["1.IMA5.IMP_IMA"]


class CHIEFErrorTask(TaskBase):
    TASK_TYPE = Task.TaskType.CHIEF_ERROR
    WB_ACTIONS = ["1.IMA6.IMP_IMA", "2.IMA6.IMP_IMA"]


class DocumentSignTask(TaskBase):
    TASK_TYPE = Task.TaskType.DOCUMENT_SIGNING
    WB_ACTIONS = ["i.AAI30.AUTH_AUTO_ISSUE", "i.G30.AUTH_ISSUE"]


class DocumentErrorTask(TaskBase):
    TASK_TYPE = Task.TaskType.DOCUMENT_ERROR
    WB_ACTIONS = ["i.AAI40.AUTH_AUTO_ISSUE", "i.G50.AUTH_ISSUE", "i.G40.AUTH_ISSUE"]


"""
Investigate print doucments tasks

1.IMA7.IMP_IMA
2.IMA7.IMP_IMA
"""
