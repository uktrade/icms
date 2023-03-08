from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView

from web.models import Exporter, Importer, User
from web.permissions import Perms


class PermissionTestHarness(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    permission_required = [Perms.page.view_permission_harness.value]  # type: ignore[attr-defined]

    http_method_names = ["get"]
    template_name = "web/perm_harness/index.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "importers": Importer.objects.filter(
                name__in=["Dummy importer", "Dummy agent for importer"]
            ),
            "exporters": Exporter.objects.filter(
                name__in=["Dummy exporter", "Dummy agent exporter"]
            ),
            "users": User.objects.filter(
                username__in=["ilb_admin", "ilb_admin_2", "importer_user", "exporter_user", "agent"]
            ),
        }
