import structlog as logging
from django.conf.urls import url
from django.urls import reverse
from viewflow.activation import STATUS
from viewflow.flow import View as ViewflowView

from .views import ReAssignTaskView

logger = logging.getLogger(__name__)


class View(ViewflowView):
    """
        Custom viewflow node with additional reassign view


        In addition to Permission can check if user is in a given team.

        Permissions are shared across all teams for  Importers, Exporter and Constabularies
        additional check required for users performing these tasks

    """

    reassign_view_class = ReAssignTaskView
    team = None

    def __init__(self, *args, **kwargs):
        """
        Instantiate a View node

        :keyword reassign_view: Overrides defeault ReAssignView for the node
        """
        self._reassign_view = kwargs.pop("reassign_view", None)
        super().__init__(*args, **kwargs)

    @property
    def reassign_view(self):
        """View to reassign task to another user"""
        return self._reassign_view if self._reassign_view else self.reassign_view_class.as_view()

    def urls(self):
        """Add /reassign/ task url"""
        urls = super().urls()
        urls.append(
            url(
                r"^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/reassign/$".format(self.name),
                self.reassign_view,
                {"flow_task": self},
                name="{}__reassign".format(self.name),
            )
        )
        return urls

    def get_task_url(self, task, url_type="guess", namespace="", **kwargs):
        """
            Handle `reassign` url_type
        """

        user = kwargs.get("user", None)

        if url_type == "reassign":
            if task.status == STATUS.ASSIGNED and self.can_execute(user, task):
                url_name = "{}:{}__reassign".format(namespace, self.name)
                return reverse(url_name, kwargs={"process_pk": task.process_id, "task_pk": task.pk})

        return super().get_task_url(task, url_type, namespace=namespace, **kwargs)
