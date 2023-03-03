from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView

from web.permissions import Perms


class PermissionTestHarness(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    permission_required = [Perms.page.view_permission_harness.value]  # type: ignore[attr-defined]

    http_method_names = ["get"]
    template_name = "web/perm_harness/index.html"
