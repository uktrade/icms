from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView

from web.domains.case.services import case_progress
from web.ecil.forms import forms_cfs as forms
from web.models import CertificateOfFreeSaleApplication, User
from web.permissions import AppChecker, Perms


def check_can_edit_application(user: User, application: CertificateOfFreeSaleApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


class CFSInProgressUpdateViewBase(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    case_progress.InProgressApplicationStatusTaskMixin,
    UpdateView,
):
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # Extra typing for clarity
    application: CertificateOfFreeSaleApplication

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True


@method_decorator(transaction.atomic, name="post")
class CFSApplicationReferenceUpdateView(CFSInProgressUpdateViewBase):
    # UpdateView config
    form_class = forms.CFSApplicationReferenceForm
    template_name = "ecil/gds_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_link_kwargs"] = {"text": "Back", "href": reverse("workbasket")}

        return context

    def get_success_url(self):
        # TODO: Add sucess url to next step.
        return reverse("workbasket")
