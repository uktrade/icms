from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from web.domains.case.export.models import CFSSchedule
from web.domains.case.services import case_progress
from web.ecil.forms import forms_cfs as forms
from web.ecil.gds import component_serializers as serializers
from web.ecil.gds import forms as gds_forms
from web.ecil.gds.views import BackLinkMixin
from web.models import CertificateOfFreeSaleApplication, User
from web.models.shared import YesNoChoices
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

        return redirect(
            reverse(
                "ecil:export-cfs:schedule-exporter-status",
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


#
# Views relating to editing CFS Schedule fields
#
@method_decorator(transaction.atomic, name="post")
class CFSScheduleBaseUpdateView(CFSInProgressRelatedObjectViewBase, BackLinkMixin, UpdateView):
    """Common base class for all views used to update a CFSSchedule field."""

    # UpdateView config
    pk_url_kwarg = "schedule_pk"
    model = CFSSchedule

    def get_queryset(self) -> QuerySet[CFSSchedule]:
        """Restrict the available schedules to the ones linked to the application."""
        return self.application.schedules.all()


class CFSScheduleExporterStatusUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleExporterStatusForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-create", kwargs={"application_pk": self.application.pk}
        )

    def get_success_url(self):
        return reverse(
            "ecil:export-cfs:schedule-manufacturer-address",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


class CFSScheduleManufacturerAddressUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleManufacturerAddressForm
    template_name = "ecil/cfs/schedule_manufacturer_address.html"

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-exporter-status",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self):
        return reverse(
            "ecil:export-cfs:schedule-brand-name-holder",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["schedule_number"] = forms.get_schedule_number(self.object)

        return context


class CFSScheduleBrandNameHolderUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleBrandNameHolderForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-manufacturer-address",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self):
        return reverse(
            "ecil:export-cfs:schedule-country-of-manufacture",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


class CFSScheduleCountryOfManufactureUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleCountryOfManufactureForm
    template_name = "ecil/cfs/schedule_country_of_manufacture.html"

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-brand-name-holder",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self):
        return reverse(
            "ecil:export-cfs:schedule-legislation",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


class CFSScheduleAddLegislationUpdateView(CFSScheduleBaseUpdateView):
    """View to add a legislation to the set of legislations linked to the schedule.

    Logic to add the legislation is in the form save method.
    """

    # UpdateView config
    form_class = forms.CFSScheduleAddLegislationForm
    template_name = "ecil/cfs/schedule_legislation.html"

    def get_back_link_url(self) -> str | None:
        match self.get_referrer_view():
            case "ecil:export-cfs:schedule-legislation-add-another":
                return reverse(
                    "ecil:export-cfs:schedule-legislation-add-another",
                    kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
                )

            case _:
                return reverse(
                    "ecil:export-cfs:schedule-country-of-manufacture",
                    kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
                )

    def get_success_url(self):
        return reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleAddAnotherLegislationFormView(
    CFSInProgressRelatedObjectViewBase, BackLinkMixin, SingleObjectMixin, FormView
):
    # SingleObjectMixin config
    pk_url_kwarg = "schedule_pk"
    model = CFSSchedule

    form_class = forms.CFSScheduleAddAnotherLegislationForm
    template_name = "ecil/cfs/schedule_legislation_add_another.html"

    def get_queryset(self) -> QuerySet[CFSSchedule]:
        """Restrict the available schedules to the ones linked to the application."""
        return self.application.schedules.all()

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)

        schedule = self.get_object()
        schedule_legislations = schedule.legislations.all()

        kwargs = {"application_pk": self.application.pk, "schedule_pk": self.object.pk}
        legislation_list = []
        for legislation in schedule_legislations:
            kwargs["legislation_pk"] = legislation.pk
            remove_link = reverse("ecil:export-cfs:schedule-legislation-remove", kwargs=kwargs)
            legislation_list.append((legislation.name, remove_link))

        context["legislation_list"] = legislation_list
        context["schedule_number"] = forms.get_schedule_number(schedule)
        context["legislation_count"] = schedule_legislations.count()

        return context

    def form_valid(self, form: forms.CFSScheduleAddAnotherLegislationForm) -> HttpResponseRedirect:
        self.object = self.get_object()
        add_another = form.cleaned_data["add_another"]

        if add_another == YesNoChoices.yes:
            redirect_to = reverse(
                "ecil:export-cfs:schedule-legislation",
                kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
            )
        else:
            redirect_to = reverse(
                "export:cfs-schedule-edit",
                kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
            )

        return redirect(redirect_to)

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-legislation",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleConfirmRemoveLegislationFormView(
    CFSInProgressRelatedObjectViewBase,
    BackLinkMixin,
    SingleObjectMixin,
    FormView,
):
    """View to confirm removal of legislation linked to an in progress CFS application.."""

    # SingleObjectMixin config
    pk_url_kwarg = "schedule_pk"
    model = CFSSchedule
    # Extra typing for clarity
    object: CFSSchedule

    # FormView config
    form_class = forms.CFSScheduleRemoveLegislationForm
    template_name = "ecil/gds_form.html"
    http_method_names = ["get", "post"]

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.set_application_and_task()
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(
        self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        self.set_application_and_task()
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[CFSSchedule]:
        """Restrict the available schedules to the ones linked to the application."""
        return self.application.schedules.all()

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["schedule"] = self.object
        kwargs["legislation"] = get_object_or_404(
            self.object.legislations, pk=self.kwargs["legislation_pk"]
        )

        return kwargs

    def form_valid(self, form: forms.CFSScheduleRemoveLegislationForm) -> HttpResponseRedirect:
        schedule: CFSSchedule = self.get_object()

        if form.cleaned_data["are_you_sure"] == YesNoChoices.yes:
            schedule.legislations.remove(form.legislation)

        return super().form_valid(form)

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self) -> str:
        if self.object.legislations.count() == 0:
            view_name = "ecil:export-cfs:schedule-legislation"
        else:
            view_name = "ecil:export-cfs:schedule-legislation-add-another"

        return reverse(
            view_name, kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk}
        )
