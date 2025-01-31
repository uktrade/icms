from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.views.generic import TemplateView, UpdateView

from web.ecil.forms import forms_new_user as forms
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
            # Fake redirect urls for now
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

        # Fake redirect urls for now
        if is_exporter_site(site):
            return reverse("workbasket")
        elif is_importer_site(site):
            return reverse("workbasket")
        else:
            return reverse("workbasket")
