import datetime as dt

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from .forms import ValidateSignatureForm


class AccessibilityStatementView(TemplateView):
    http_method_names = ["get"]
    template_name = "web/support/accessibility_statement.html"


class SupportLandingView(TemplateView):
    http_method_names = ["get"]
    template_name = "web/support/index.html"


class ValidateSignatureView(FormView):
    form_class = ValidateSignatureForm
    template_name = "web/support/signatures/validate.html"

    def form_valid(self, form: ValidateSignatureForm) -> HttpResponse:
        date_issued = form.cleaned_data["date_issued"]
        if date_issued >= dt.date(2024, 9, 26):
            return redirect(reverse("support:validate-signature-v2"))
        return redirect(reverse("support:validate-signature-v1"))


class ValidateSignatureV1View(TemplateView):
    http_method_names = ["get"]
    template_name = "web/support/signatures/validate_v1.html"


class ValidateSignatureV2View(TemplateView):
    http_method_names = ["get"]
    template_name = "web/support/signatures/validate_v2.html"
