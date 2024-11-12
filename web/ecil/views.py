from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView

from web.permissions import Perms


class GDSTestPage(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "ecil/gds_test_page.html"
