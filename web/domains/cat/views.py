from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView

from web.domains.user.models import User

from .forms import SearchCATForm


class CATListView(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "web/domains/cat/list.html"

    def has_permission(self) -> bool:
        user: User = self.request.user

        ilb_admin = user.has_perm("web.reference_data_access")
        exporter_user = user.has_perm("web.exporter_access")

        return ilb_admin or exporter_user

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Certificate Application Templates"
        context["form"] = SearchCATForm()

        return context
