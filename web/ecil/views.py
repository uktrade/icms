from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import FormView, ListView, TemplateView

from web.ecil.gds.views import FormStep, MultiStepFormSummaryView, MultiStepFormView
from web.models import ECILMultiStepExample
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


class ECILMultiStepFormView(LoginRequiredMixin, PermissionRequiredMixin, MultiStepFormView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # MultiStepFormView config
    form_steps = {
        "one": FormStep(form_cls=forms.ExampleMultiStepStepOneForm),
        "two": FormStep(form_cls=forms.ExampleMultiStepStepTwoForm),
        "three": FormStep(form_cls=forms.ExampleMultiStepStepThreeForm),
    }
    cache_prefix = "ECILMultiStepFormView"
    template_name = "ecil/gds_step_form.html"

    def get_previous_step_url(self) -> str:
        return reverse("ecil:step_form", kwargs={"step": self.previous_step})

    def get_next_step_url(self) -> str:
        return reverse("ecil:step_form", kwargs={"step": self.next_step})

    def get_summary_url(self) -> str:
        return reverse("ecil:step_form_summary")


class ECILMultiStepFormSummaryView(
    LoginRequiredMixin, PermissionRequiredMixin, MultiStepFormSummaryView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # MultiStepFormSummaryView config
    edit_view = ECILMultiStepFormView
    form_class = forms.ExampleMultiStepStepSummaryForm
    template_name = "ecil/gds_summary_list.html"
    http_method_names = ["get", "post"]

    def get_display_value(self, field: str, value: Any) -> str:
        m = ECILMultiStepExample(**{field: value})

        if hasattr(m, f"get_{field}_display"):
            if display_value := getattr(m, f"get_{field}_display")():
                return display_value

        return super().get_display_value(field, value)

    def get_edit_step_url(self, step: str) -> str:
        return reverse("ecil:step_form", kwargs={"step": step})

    def get_success_url(self) -> str:
        return reverse("ecil:multi_step_model_list")


class ECILMultiStepExampleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # ListView config
    model = ECILMultiStepExample
    template_name = "ecil/list.html"
