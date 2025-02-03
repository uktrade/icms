from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView, UpdateView

from web.ecil.forms import forms_new_user as forms
from web.ecil.gds import forms as gds_forms
from web.models import User
from web.permissions import Perms
from web.sites import is_exporter_site, is_importer_site


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
            # TODO: Fake redirect urls for now
            "auth_login_url": reverse("ecil:new_user:update_name"),
        }


class NewUserUpdateNameView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """View shown after a new user is redirected back to ECIL from GOV.UK One Login."""

    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    form_class = forms.OneLoginNewUserUpdateForm
    template_name = "ecil/new_user/update_name.html"

    def get_object(self, queryset: QuerySet | None = None) -> User:
        return User.objects.get(pk=self.request.user.pk)

    def get_success_url(self) -> str:
        site = self.request.site

        # TODO: Fake redirect urls for now
        if is_exporter_site(site):
            return reverse("ecil:new_user:exporter_triage")
        elif is_importer_site(site):
            return reverse("workbasket")
        else:
            return reverse("workbasket")


class NewUserExporterTriageFormView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    form_class = forms.ExporterTriageForm
    template_name = "ecil/new_user/exporter_triage_form.html"

    def form_valid(self, form: forms.ExporterTriageForm) -> HttpResponseRedirect:
        applications = form.cleaned_data["applications"]

        if applications == [gds_forms.GovUKCheckboxesField.NONE_OF_THESE]:
            self.success_url = reverse("ecil:new_user:something_else")
        else:
            # TODO: Fake redirect urls for now
            self.success_url = reverse("workbasket")

        return super().form_valid(form)


class NewUserExporterTriageSomethingElseView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # TemplateView
    http_method_names = ["get"]
    template_name = "ecil/new_user/exporter_triage_something_else.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context | {
            "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        }
