from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.utils.decorators import method_decorator
from django_ratelimit import UNSAFE
from django_ratelimit.decorators import ratelimit

from web.ecil.forms import forms_access_requests as forms
from web.ecil.gds.views import FormStep, MultiStepFormView
from web.permissions import Perms
from web.sites import require_exporter


@method_decorator(require_exporter(check_permission=False), name="dispatch")
@method_decorator(ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE), name="post")
class ExporterAccessRequestMultiStepFormView(
    LoginRequiredMixin, PermissionRequiredMixin, MultiStepFormView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # MultiStepFormView config
    form_steps = {
        "exporter-or-agent": FormStep(form_cls=forms.ExporterAccessRequestTypeForm),
        "company-details": FormStep(
            form_cls=forms.ExporterAccessRequestCompanyDetailsForm,
            template_name="ecil/access_request/exporter_company_details-step.html",
        ),
        "company-purpose": FormStep(form_cls=forms.ExporterAccessRequestCompanyPurposeForm),
        "company-products": FormStep(form_cls=forms.ExporterAccessRequestCompanyProductsForm),
    }

    template_name = "ecil/access_request/exporter_step_form.html"

    def get_previous_step_url(self) -> str:
        return reverse(
            "ecil:access_request:exporter_step_form", kwargs={"step": self.previous_step}
        )

    def get_next_step_url(self) -> str:
        return reverse("ecil:access_request:exporter_step_form", kwargs={"step": self.next_step})

    # def get_summary_url(self) -> str:
    #     return reverse("ecil:access_request:exporter_step_form")
