from web.flow.models import Task


class WorkbasketBase:
    """Base class for every Process subclass that wants to be shown in the workbasket."""

    def get_workbasket_template(self) -> str:
        """Get name of template file to use for workbasket."""

        raise NotImplementedError

    def get_task_url(self, task: Task, user) -> str:
        """Get URL for the given task (and user)."""

        raise NotImplementedError
