from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from web.permissions import Perms

from . import forms


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
    form_class = forms.ExampleGDSForm
    template_name = "ecil/gds_form.html"

    def get_success_url(self):
        return reverse("ecil:gds_form_example")


class GDSModelFormView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # FormView config
    form_class = forms.ExampleGDSModelForm
    template_name = "ecil/gds_model_form.html"

    def get_success_url(self):
        return reverse("ecil:gds_model_form_example")


class GDSConditionalModelFormView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # FormView config
    form_class = forms.ExampleConditionalGDSModelForm
    template_name = "ecil/gds_model_form.html"

    def get_success_url(self):
        return reverse("ecil:gds_conditional_model_form_example")
