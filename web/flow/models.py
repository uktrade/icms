from typing import List, Union

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet

from . import errors


class Process(models.Model):
    """Base class for all processes."""

    process_type = models.CharField(max_length=50)

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

        if isinstance(expected_state, list):
            if self.status not in expected_state:
                raise errors.ProcessStateError(f"Process is in the wrong state: {self.status}")
        else:
            if self.status != expected_state:
                raise errors.ProcessStateError(f"Process is in the wrong state: {self.status}")

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


class Task(models.Model):
    """A task. A process can have as many tasks as it wants attached to it, and
    tasks maintain a "previous" link to track the task ordering.

    NOTE: a task can have multiple child tasks, but only one parent task.
    """

    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name="tasks")

    task_type = models.CharField(max_length=30)

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

    def __unicode__(self):
        return f"{self.id}"

    def __str__(self):
        return f"{self.id}"
