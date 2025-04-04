from typing import Any
from urllib import parse

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import Resolver404, ResolverMatch, resolve, reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, FormView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from web.domains.case.services import application as applicant_application
from web.domains.case.services import case_progress
from web.ecil.forms import forms_export_application as forms
from web.ecil.gds import component_serializers as serializers
from web.ecil.gds.views import BackLinkMixin, SummaryUpdateView
from web.ecil.types import EXPORT_APPLICATION
from web.flow.models import ProcessTypes
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    Country,
    ECILUserExportApplication,
    ExportApplicationType,
    Office,
    User,
)
from web.models.shared import YesNoChoices
from web.permissions import AppChecker, Perms, can_user_edit_org
from web.types import AuthenticatedHttpRequest


#
# Views relating to creating an export application
#
class CreateExportApplicationStartTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "ecil/export_application/start.html"
    extra_context = {
        "pick_app_type_url": reverse_lazy("ecil:export-application:application-type"),
    }


class CreateExportApplicationBase(LoginRequiredMixin, PermissionRequiredMixin, BackLinkMixin):
    """Common base class for all views used to create a ECILUserExportApplication record.

    Does the following:
        - Defines the required permissions.
        - Retrieves the correct ECILUserExportApplication record.
        - Inherits from BackLinkMixin
    """

    # PermissionRequiredMixin config
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # Extra typing for clarity
    object: ECILUserExportApplication

    def get_object(self, queryset: QuerySet | None = None) -> ECILUserExportApplication:
        instance, _ = ECILUserExportApplication.objects.get_or_create(
            created_by=self.request.user,
        )

        return instance


class CreateExportApplicationAppTypeFormView(CreateExportApplicationBase, UpdateView):
    # UpdateView config
    form_class = forms.ExportApplicationTypeForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str:
        if self.from_summary:
            return reverse("ecil:export-application:summary")

        return reverse("ecil:export-application:new")

    def get_success_url(self) -> str:
        return reverse("ecil:export-application:exporter")


class CreateExportApplicationExporterFormView(CreateExportApplicationBase, UpdateView):
    # UpdateView config
    form_class = forms.ExportApplicationExporterForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str:
        if self.from_summary:
            return reverse("ecil:export-application:summary")

        return reverse("ecil:export-application:application-type")

    def get_success_url(self) -> str:
        # Valid options are either an exporter or None if "Another Company" has been selected
        if self.object.exporter:
            return reverse("ecil:export-application:exporter-office")
        else:
            return reverse("ecil:export-application:another-exporter")


class CreateExportApplicationExporterOfficeFormView(CreateExportApplicationBase, UpdateView):
    # UpdateView config
    form_class = forms.ExportApplicationExporterOfficeForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str:
        if self.from_summary:
            return reverse("ecil:export-application:summary")

        return reverse("ecil:export-application:exporter")

    def get_success_url(self) -> str:
        # Valid options are either an office or None if "Another Office" has been selected
        if self.object.exporter_office:
            response_url = reverse("ecil:export-application:summary")
        else:
            exporter = self.object.exporter
            if exporter and can_user_edit_org(self.request.user, exporter):
                response_url = reverse("ecil:export-application:exporter-office-add")
            else:
                response_url = reverse("ecil:export-application:another-exporter-office")

        return response_url


@method_decorator(transaction.atomic, name="post")
class CreateExportApplicationSummaryUpdateView(CreateExportApplicationBase, SummaryUpdateView):
    # UpdateView config
    form_class = forms.CreateExportApplicationSummaryForm
    template_name = "ecil/gds_summary_list.html"
    http_method_names = ["get", "post"]
    extra_context = {
        "h1_content": "Your details and certificate details",
        "below_h1_content": (
            "Check your details and the certificate details you have given are correct"
        ),
    }

    def get_summary_items(self, context: dict[str, Any]) -> dict[str, serializers.summary_list.Row]:
        submit_form = context["form"]

        if self.object.exporter:
            selected_exporter = self.object.exporter.name
        else:
            selected_exporter = ""

        if self.object.exporter_office:
            office_choices = dict(submit_form.fields["exporter_office"].choices)
            selected_office = office_choices.get(self.object.exporter_office.pk, "")
        else:
            selected_office = ""

        rows = [
            (
                "app_type",
                self.object.get_app_type_display(),
                reverse("ecil:export-application:application-type"),
            ),
            ("exporter", selected_exporter, reverse("ecil:export-application:exporter")),
            (
                "exporter_office",
                selected_office,
                reverse("ecil:export-application:exporter-office"),
            ),
        ]

        items = {}
        for field, display_value, edit_link in rows:
            key = submit_form[field].label
            items[field] = self.get_summary_item_row(field, key, display_value, edit_link)

        return items

    def form_valid(self, form: forms.CreateExportApplicationSummaryForm) -> HttpResponseRedirect:
        # Shouldn't actually change anything
        self.object = form.save()

        match self.object.app_type:
            case self.object.ExportApplicationsChoices.CFS:
                model_class = CertificateOfFreeSaleApplication
                application_type = ExportApplicationType.objects.get(
                    type_code=ExportApplicationType.Types.FREE_SALE
                )

            case self.object.ExportApplicationsChoices.COM:
                model_class = CertificateOfManufactureApplication
                application_type = ExportApplicationType.objects.get(
                    type_code=ExportApplicationType.Types.MANUFACTURE
                )

            case self.object.ExportApplicationsChoices.GMP:
                model_class = CertificateOfGoodManufacturingPracticeApplication
                application_type = ExportApplicationType.objects.get(
                    type_code=ExportApplicationType.Types.GMP
                )

            case _:
                raise ValueError(
                    f"Unable to create application for app_type: {self.object.app_type}"
                )

        # Create the correct application
        self.application = applicant_application.create_export_application(
            self.request,
            model_class,
            application_type,
            self.object.exporter,
            self.object.exporter_office,
            self.object.agent,
            self.object.agent_office,
        )

        # Clear the ECILUserExportApplication record
        self.object.delete()

        return redirect(self.get_success_url())

    def get_back_link_url(self) -> str:
        return reverse("ecil:export-application:exporter-office")

    def get_success_url(self) -> str:
        kwargs = {"application_pk": self.application.pk}

        match self.object.app_type:
            case self.object.ExportApplicationsChoices.CFS:
                response_url = reverse("ecil:export-cfs:application-reference", kwargs=kwargs)
            case (
                self.object.ExportApplicationsChoices.COM
                | self.object.ExportApplicationsChoices.GMP
            ):
                response_url = reverse(self.application.get_edit_view_name(), kwargs=kwargs)
            case _:
                response_url = reverse("workbasket")

        return response_url


class CreateExportApplicationExporterOfficeCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, BackLinkMixin, CreateView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # CreateView config
    model = Office
    form_class = forms.ExportApplicationNewExporterOfficeForm
    template_name = "ecil/gds_form.html"

    def get_user_export_application(self) -> ECILUserExportApplication:
        instance, _ = ECILUserExportApplication.objects.get_or_create(
            created_by=self.request.user,
        )

        return instance

    def has_permission(self) -> bool:
        has_user_perms = super().has_permission()

        self.exporter = self.get_user_export_application().exporter

        return (
            has_user_perms and self.exporter and can_user_edit_org(self.request.user, self.exporter)
        )

    def form_valid(
        self, form: forms.ExportApplicationNewExporterOfficeForm
    ) -> HttpResponseRedirect:
        office = form.save(commit=False)
        office.address_entry_type = Office.MANUAL
        office.save()

        self.exporter.offices.add(office)

        return redirect(self.get_success_url())

    def get_back_link_url(self) -> str:
        return reverse("ecil:export-application:exporter-office")

    def get_success_url(self) -> str:
        return reverse("ecil:export-application:exporter-office")


class CreateExportApplicationAnotherExporterTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, BackLinkMixin, TemplateView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "ecil/export_application/another_exporter.html"
    extra_context = {
        "create_access_request_url": reverse_lazy("ecil:access_request:new"),
    }

    def get_back_link_url(self) -> str:
        return reverse("ecil:export-application:exporter")


class CreateExportApplicationAnotherExporterOfficeTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, BackLinkMixin, TemplateView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "ecil/export_application/another_exporter_office.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["notification_banner_kwargs"] = (
            serializers.notification_banner.NotificationBannerKwargs(
                text="You need permission to add an address",
            ).model_dump(exclude_defaults=True)
        )

        return context

    def get_back_link_url(self) -> str:
        return reverse("ecil:export-application:exporter-office")


class CreateExportApplicationAnotherContactTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # TemplateView
    http_method_names = ["get"]
    template_name = "ecil/export_application/another_contact.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["notification_banner_kwargs"] = (
            serializers.notification_banner.NotificationBannerKwargs(
                text=(
                    "If you want someone else to be the main contact for the application,"
                    " they need to be linked to the exporter"
                ),
            ).model_dump(exclude_defaults=True)
        )

        referrer_view = self.request.session.get("referrer_view")
        referrer_view_kwargs = self.request.session.get("referrer_view_kwargs")

        if referrer_view and referrer_view_kwargs:
            url = reverse(referrer_view, kwargs=referrer_view_kwargs)
            context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
                text="Back", href=url
            ).model_dump(exclude_defaults=True)

        return context

    # TODO: Revisit in ECIL-638 (HTTP_REFERER view mixin / middleware)
    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Store the referrer url for back link
        referrer = self.request.META.get("HTTP_REFERER", "")
        referrer_path: str = parse.urlparse(referrer).path

        try:
            resolver_match: ResolverMatch = resolve(referrer_path)
            self.request.session["referrer_view"] = resolver_match.view_name
            if resolver_match.kwargs:
                self.request.session["referrer_view_kwargs"] = resolver_match.kwargs

        except Resolver404:
            pass

        return super().get(request, *args, **kwargs)


#
# Views relating to editing an in progress export application
#
def check_can_edit_application(user: User, application: EXPORT_APPLICATION) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


class ExportApplicationInProgressViewBase(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    case_progress.InProgressApplicationStatusTaskMixin,
):
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # Extra typing for clarity
    application: EXPORT_APPLICATION

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True


class ExportApplicationInProgressRelatedObjectViewBase(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    case_progress.InProgressApplicationRelatedObjectStatusTaskMixin,
):
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # Extra typing for clarity
    application: EXPORT_APPLICATION

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True


@method_decorator(transaction.atomic, name="post")
class ExportApplicationExportCountriesUpdateView(ExportApplicationInProgressViewBase, UpdateView):
    # UpdateView config
    form_class = forms.ExportApplicationExportCountriesForm
    template_name = "ecil/export_application/export_countries.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        country_qs = self.application.countries.all()
        context["export_countries"] = country_qs

        if country_qs:
            if country_qs.count() > 1:
                caption = f"You have added {country_qs.count()} countries or territories"
            else:
                caption = "You have added 1 country or territory"

            rows = []
            for pk, name in country_qs.values_list("pk", "name", named=True):
                remove_country_url = reverse(
                    "ecil:export-application:countries-remove",
                    kwargs={
                        "application_pk": self.application.pk,
                        "country_pk": pk,
                    },
                )
                link = f'<a href="{remove_country_url}" class="govuk-link govuk-link--no-visited-state">Remove</a>'

                rows.append(
                    [
                        serializers.table.RowItem(text=name),
                        serializers.table.RowItem(html=link, classes="govuk-!-text-align-right"),
                    ]
                )

            context["govuk_table_kwargs"] = serializers.table.TableKwargs(
                caption=caption,
                captionClasses="govuk-table__caption--m",
                firstCellIsHeader=False,
                rows=rows,
            ).model_dump(exclude_defaults=True)

            match self.application.process_type:
                case ProcessTypes.CFS:
                    next_url = reverse(
                        "ecil:export-cfs:schedule-create",
                        kwargs={"application_pk": self.application.pk},
                    )
                case _:
                    next_url = reverse("workbasket")

            context["next_url"] = next_url

        # TODO: ECIL-683 Fix the hardcoded previous URL in another story.
        #       This view is a common view for all export apps, it needs to go back to correct view
        previous_step_url = reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.application.pk}
        )
        context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
            text="Back", href=previous_step_url
        ).model_dump(exclude_defaults=True)

        return context

    def form_valid(self, form: forms.ExportApplicationExportCountriesForm) -> HttpResponseRedirect:
        country = form.cleaned_data["countries"]

        self.application.countries.add(country)
        self.application.save()

        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.application.pk}
        )


@method_decorator(transaction.atomic, name="post")
class ExportApplicationConfirmRemoveCountryFormView(
    ExportApplicationInProgressRelatedObjectViewBase, SingleObjectMixin, FormView
):
    """View to confirm removal of export countries linked to an in progress export application."""

    # SingleObjectMixin config
    model = Country
    pk_url_kwarg = "country_pk"
    object: Country | None = None

    # FormView config
    form_class = forms.ExportApplicationRemoveExportCountryForm
    template_name = "ecil/gds_form.html"
    http_method_names = ["get", "post"]

    def get_queryset(self) -> QuerySet[Country]:
        return self.application.countries.all()

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["country"] = self.get_object()

        return kwargs

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["back_link_kwargs"] = serializers.back_link.BackLinkKwargs(
            text="Back", href=self.get_success_url()
        ).model_dump(exclude_defaults=True)

        return context

    def form_valid(
        self, form: forms.ExportApplicationRemoveExportCountryForm
    ) -> HttpResponseRedirect:

        if form.cleaned_data["are_you_sure"] == YesNoChoices.yes:
            self.application.countries.remove(form.country)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.application.pk}
        )
