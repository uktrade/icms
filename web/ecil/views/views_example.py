from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView, FormView, ListView, TemplateView

from web.ecil.forms import forms_example as forms
from web.ecil.gds import component_serializers as serializers
from web.ecil.gds.views import FormStep, MultiStepFormSummaryView, MultiStepFormView
from web.models import ECILExample, ECILMultiStepExample
from web.permissions import Perms


class GDSTestPageView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "ecil/example/test_page.html"


class GDSFormView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # FormView config
    form_class = forms.ExampleGDSForm
    template_name = "ecil/example/form.html"

    def get_success_url(self) -> str:
        return reverse("ecil:example:gds_form_example")


class GDSModelFormCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # UpdateView config
    model = ECILExample
    form_class = forms.ExampleGDSModelForm
    template_name = "ecil/gds_form.html"

    def get_success_url(self) -> str:
        return reverse("ecil:example:ecil_example_list")


class ECILExampleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # ListView config
    model = ECILExample
    template_name = "ecil/example/list.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
            text="Back", href=reverse("ecil:example:gds_model_form_example")
        ).model_dump(exclude_defaults=True)

        return context


class GDSConditionalModelFormView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # FormView config
    form_class = forms.ExampleConditionalGDSModelForm
    template_name = "ecil/gds_form.html"

    def get_success_url(self) -> str:
        return reverse("ecil:example:gds_conditional_model_form_example")


class ECILMultiStepFormView(LoginRequiredMixin, PermissionRequiredMixin, MultiStepFormView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # MultiStepFormView config
    form_steps = {
        "one": FormStep(form_cls=forms.ExampleMultiStepStepOneForm),
        "two": FormStep(form_cls=forms.ExampleMultiStepStepTwoForm),
        "three": FormStep(form_cls=forms.ExampleMultiStepStepThreeForm),
    }
    template_name = "ecil/gds_form.html"

    def get_previous_step_url(self) -> str:
        return reverse("ecil:example:step_form", kwargs={"step": self.previous_step})

    def get_next_step_url(self) -> str:
        return reverse("ecil:example:step_form", kwargs={"step": self.next_step})

    def get_summary_url(self) -> str:
        return reverse("ecil:example:step_form_summary")


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

    def form_valid_save_hook(self) -> None:
        self.new_object.created_by = self.request.user

    def get_display_value(self, field: str, value: Any) -> str:
        m = ECILMultiStepExample(**{field: value})

        if hasattr(m, f"get_{field}_display"):
            if display_value := getattr(m, f"get_{field}_display")():
                return display_value

        return super().get_display_value(field, value)

    def get_edit_step_url(self, step: str) -> str:
        return reverse("ecil:example:step_form", kwargs={"step": step})

    def get_success_url(self) -> str:
        return reverse("ecil:example:multi_step_model_list")


class ECILMultiStepExampleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # ListView config
    model = ECILMultiStepExample
    template_name = "ecil/example/list.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
            text="Back", href=reverse("ecil:example:step_form", kwargs={"step": "one"})
        ).model_dump(exclude_defaults=True)

        return context
