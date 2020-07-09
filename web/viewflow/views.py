#!/usr/bin/env python
# -*- coding: utf-8 -*-
import structlog as logging
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.views.generic import TemplateView
from six.moves.urllib.parse import quote as urlquote
from viewflow.activation import STATUS
from viewflow.decorators import flow_view
from viewflow.flow.views import CancelProcessView as ViewflowCancelProcessView
from viewflow.flow.views.mixins import MessageUserMixin
from viewflow.models import Subprocess

from web.auth.utils import get_team_members_with_permission, get_users_with_permission
from web.domains.user.models import User

from .forms import ReAssignTaskForm

logger = logging.getLogger(__name__)


class CancelProcessView(ViewflowCancelProcessView):
    """
        A customised Viewflow cancel process view to allow cancelling process
        by unassigning all process tasks

        Viewflow doesn't allow cancelling of processes with active tasks assigned to
        users

    """

    def _unassign_tasks(self, process):
        """
            Unassign all active subprocess tasks

        """
        assigned_tasks = process.task_set.filter(status=STATUS.ASSIGNED)
        for task in assigned_tasks:
            activation = task.activate()
            activation.unassign()

    def _finish_parent_task(self, task):
        """
            Finish subprocess parent task when subprocess in cancelled
        """
        activation = task.activate()
        activation.done()

    def post(self, request, *args, **kwargs):
        """
            Cancel process. Unassign all process tasks before
            cancelling

            If a this is a subprocess finish parent task of the parent process
            (Subprocesses in Viewflow are children of tasks in a parent process)
        """

        process = self.get_object()
        # Viewflow doesn't allow cancelling unless all
        # process tasks are unassigned
        self._unassign_tasks(process)
        if isinstance(process, Subprocess):
            # Finish parent task if this is a sub process
            self._finish_parent_task(process.parent_task)

        return super().post(request, *args, **kwargs)


class ReAssignTaskView(MessageUserMixin, TemplateView):
    """
    Default re-assign view for flow task.
    Only allows re-assigning to users the task are available to

    Get confirmation from user, re-assigns task and redirects to task detail
    """

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)

    action_name = "reassign"

    def get_template_names(self):
        """List of template names to be used for a task reassign page

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/<task_name>_reassign.html,
             <app_label>/<flow_label>/task_reassign.html,
             'viewflow/flow/task_reassign.html']
        """
        if self.template_name is None:
            flow_task = self.activation.flow_task
            opts = self.activation.flow_class._meta

            return (
                "{}/{}/{}_reassign.html".format(opts.app_label, opts.flow_label, flow_task.name),
                "{}/{}/task_reassign.html".format(opts.app_label, opts.flow_label),
                "viewflow/flow/task_reassign.html",
            )
        else:
            return [self.template_name]

    def get_user_queryset(self):
        """
        Get list of users to select from to assign the task to
        """
        permission = self.activation.task.owner_permission
        if self.team:
            return get_team_members_with_permission(self.team, permission).filter(is_active=True)
        else:
            return get_users_with_permission(permission).filter(is_active=True)

    def get_form(self):
        return ReAssignTaskForm(self.get_user_queryset(), data=self.request.POST or None)

    def get_context_data(self, **kwargs):
        """Context for a reassign view.

        :keyword users: list of users the task can be assigned to
        """
        context = super().get_context_data(**kwargs)
        context["activation"] = self.activation
        context["form"] = self.get_form()
        return context

    def get_success_url(self):
        """Continue on task or redirect back to task list."""

        url = self.activation.flow_task.get_task_url(
            self.activation.task,
            url_type="guess",
            user=self.request.user,
            namespace=self.request.resolver_match.namespace,
        )

        back = self.request.GET.get("back", None)
        if back and not is_safe_url(url=back, allowed_hosts={self.request.get_host()}):
            back = "/"

        if "_continue" in self.request.POST and back:
            url = "{}?back={}".format(url, urlquote(back))
        elif back:
            url = back

        return url

    def post(self, request, *args, **kwargs):
        """
        ReAssign task to the slected user.

        Expect that form submitted with `_continue` or `_reassign` button::

            <button type="submit" name="_continue">Assign and continue on this process</button>
            <button type="submit" name="_reassign">Assign</button>
        """
        form = self.get_form()
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        if "_reassign" or "_continue" in request.POST:
            user = User.objects.get(pk=form.data.get("user"))
            self.activation.reassign(user)
            self.success("Task {task} has been reassigned")
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    @method_decorator(flow_view)
    def dispatch(self, request, *args, **kwargs):
        """Check permissions and reassign task to the another user."""
        self.activation = request.activation

        if request.user is None or request.user.is_anonymous:
            raise PermissionDenied

        if not self.activation.reassign.can_proceed():
            self.error("Task {task} cannot be reassigned")
            return redirect(
                self.activation.flow_task.get_task_url(
                    self.activation.task,
                    url_type="detail",
                    user=request.user,
                    namespace=self.request.resolver_match.namespace,
                )
            )

        if not self.activation.flow_task.can_execute(request.user, self.activation.task):
            raise PermissionDenied

        return super(ReAssignTaskView, self).dispatch(request, *args, **kwargs)
