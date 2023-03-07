from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView

from web.models import Exporter, Importer
from web.permissions import Perms


class PermissionTestHarness(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    permission_required = [Perms.page.view_permission_harness.value]  # type: ignore[attr-defined]

    http_method_names = ["get"]
    template_name = "web/perm_harness/index.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "dummy_importer": Importer.objects.get(name="Dummy importer"),
            "dummy_exporter": Exporter.objects.get(name="Dummy exporter"),
            "importers": Importer.objects.filter(is_active=True),
            "exporters": Exporter.objects.filter(is_active=True),
        }
