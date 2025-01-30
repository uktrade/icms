from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView

from web.permissions import Perms


# TODO: This module will probably be renamed / removed. It hold views that will be hooked up to the login path when ready
class ExporterLoginStartView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # TemplateView
    http_method_names = ["get"]
    template_name = "ecil/new_user/exporter_login_start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context | {
            # Fake login for now
            "auth_login_url": reverse("workbasket"),
        }
