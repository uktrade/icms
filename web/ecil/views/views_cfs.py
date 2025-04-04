from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, UpdateView

from web.domains.case.export.models import CFSSchedule
from web.domains.case.services import case_progress
from web.ecil.forms import forms_cfs as forms
from web.ecil.gds import component_serializers as serializers
from web.ecil.gds import forms as gds_forms
from web.models import CertificateOfFreeSaleApplication, User
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest


def check_can_edit_application(user: User, application: CertificateOfFreeSaleApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


class CFSInProgressViewBase(
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


class CFSInProgressRelatedObjectViewBase(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    case_progress.InProgressApplicationRelatedObjectStatusTaskMixin,
):
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # Extra typing for clarity
    application: CertificateOfFreeSaleApplication

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True


@method_decorator(transaction.atomic, name="post")
class CFSApplicationReferenceUpdateView(CFSInProgressViewBase, UpdateView):
    # UpdateView config
    form_class = forms.CFSApplicationReferenceForm
    template_name = "ecil/gds_form.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
            text="Back", href=reverse("workbasket")
        ).model_dump(exclude_defaults=True)

        return context

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.application.pk}
        )


@method_decorator(transaction.atomic, name="post")
class CFSApplicationContactUpdateView(CFSInProgressViewBase, UpdateView):
    # UpdateView config
    form_class = forms.CFSApplicationContactForm
    template_name = "ecil/gds_form.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        previous_step_url = reverse(
            "ecil:export-cfs:application-reference", kwargs={"application_pk": self.application.pk}
        )
        context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
            text="Back", href=previous_step_url
        ).model_dump(exclude_defaults=True)

        return context

    def form_valid(self, form: forms.CFSApplicationContactForm) -> HttpResponseRedirect:
        contact = form.cleaned_data["contact"]

        if contact == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            self.application.contact = None
            self.application.save()

            return redirect(reverse("ecil:export-application:another-contact"))

        self.application.contact = contact
        self.application.save()

        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.application.pk}
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleCreateView(CFSInProgressRelatedObjectViewBase, TemplateView):
    # TemplateView config
    http_method_names = ["get", "post"]
    template_name = "ecil/cfs/schedule_create.html"

    def post(
        self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        self.set_application_and_task()

        # TODO: When the cfs app is created it already creates a schedule.
        #       Decide how this should work (V2 isn't the same as v3).
        new_schedule = CFSSchedule.objects.create(
            application=self.application, created_by=request.user
        )

        # TODO: Redirect to next V3 view - Not the old schedule edit view.
        return redirect(
            reverse(
                "export:cfs-schedule-edit",
                kwargs={"application_pk": self.application.pk, "schedule_pk": new_schedule.pk},
            )
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        previous_step_url = reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.application.pk}
        )
        context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
            text="Back", href=previous_step_url
        ).model_dump(exclude_defaults=True)

        context["create_schedule_btn_kwargs"] = serializers.button.ButtonKwargs(
            text="Create a product schedule",
            type="submit",
            isStartButton=True,
            preventDoubleClick=True,
        ).model_dump(exclude_defaults=True)

        return context
