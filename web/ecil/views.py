from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from web.permissions import Perms

from .forms import GDSForm


class GDSTestPageView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "ecil/gds_test_page.html"


class GDSFormView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # FormView config
    form_class = GDSForm
    template_name = "ecil/gds_form.html"

    def get_success_url(self):
        return reverse("ecil:gds_form_example")
