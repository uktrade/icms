from typing import Any
from urllib import parse

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import Resolver404, ResolverMatch, resolve, reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, FormView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from web.domains.case.services import case_progress
from web.ecil.forms import forms_export_application as forms
from web.ecil.gds import component_serializers as serializers
from web.ecil.gds import forms as gds_forms
from web.ecil.gds.views import BackLinkMixin, SessionFormView
from web.ecil.types import EXPORT_APPLICATION
from web.flow.models import ProcessTypes
from web.models import Country, Exporter, Office, User
from web.models.shared import YesNoChoices
from web.permissions import AppChecker, Perms, can_user_edit_org
from web.types import AuthenticatedHttpRequest


#
# Views relating to creating an export application
#
class CreateExportApplicationBaseView(LoginRequiredMixin, PermissionRequiredMixin):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]


class CreateExportApplicationStartTemplateView(CreateExportApplicationBaseView, TemplateView):
    # TemplateView
    http_method_names = ["get"]
    template_name = "ecil/export_application/start.html"

    extra_context = {
        "pick_app_type_url": reverse_lazy("ecil:export-application:application-type"),
    }


class CreateExportApplicationAppTypeFormView(
    CreateExportApplicationBaseView, BackLinkMixin, SessionFormView
):
    # SessionFormView config
    form_class = forms.ExportApplicationTypeForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str:
        return reverse("ecil:export-application:new")

    def get_success_url(self):
        return reverse("ecil:export-application:exporter")


class CreateExportApplicationExporterFormView(
    CreateExportApplicationBaseView, BackLinkMixin, SessionFormView
):
    # SessionFormView config
    form_class = forms.ExportApplicationExporterForm
    template_name = "ecil/gds_form.html"

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()

        return kwargs | {"user": self.request.user}

    def get_back_link_url(self) -> str:
        return reverse("ecil:export-application:application-type")

    def form_valid(self, form: forms.ExportApplicationExporterForm) -> HttpResponseRedirect:
        self.save_form_in_session(form)

        exporter = form.cleaned_data["exporter"]

        if exporter == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            response_url = reverse("ecil:export-application:another-exporter")
        else:
            response_url = self.get_success_url()

        return redirect(response_url)

    def get_success_url(self):
        return reverse("ecil:export-application:exporter-office")


class CreateExportApplicationExporterOfficeFormView(
    CreateExportApplicationBaseView, BackLinkMixin, SessionFormView
):
    # SessionFormView config
    form_class = forms.ExportApplicationExporterOfficeForm
    template_name = "ecil/gds_form.html"

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()

        return kwargs | {
            "user": self.request.user,
            "exporter_pk": self._get_exporter().pk,
        }

    def get_back_link_url(self) -> str:
        return reverse("ecil:export-application:exporter")

    def form_valid(self, form: forms.ExportApplicationExporterOfficeForm) -> HttpResponseRedirect:
        self.save_form_in_session(form)

        office = form.cleaned_data["office"]

        if office == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            exporter = self._get_exporter()

            if can_user_edit_org(self.request.user, exporter):
                response_url = reverse("ecil:export-application:export-office-add")
            else:
                response_url = reverse("ecil:export-application:another-exporter-office")
        else:
            response_url = self.get_success_url()

        return redirect(response_url)

    def get_success_url(self):
        # TODO: Replace with next correct step.
        return reverse("ecil:export-application:new")

    def _get_exporter(self) -> Exporter:
        # Load the chosen exporter from the session
        exporter_key = CreateExportApplicationExporterFormView.get_field_key("exporter")
        exporter_pk = self.get_session_value(exporter_key)

        return Exporter.objects.get(pk=exporter_pk)


class CreateExportApplicationExporterOfficeCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, BackLinkMixin, CreateView
):
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]
    model = Office
    form_class = forms.ExportApplicationNewExporterOfficeForm
    template_name = "ecil/gds_form.html"

    def has_permission(self):
        has_user_perms = super().has_permission()

        try:
            exporter_key = CreateExportApplicationExporterFormView.get_field_key("exporter")
            exporter_pk = self.request.session.get(exporter_key, None)
            self.exporter = Exporter.objects.get(pk=exporter_pk)

        except ObjectDoesNotExist:
            return False

        return has_user_perms and can_user_edit_org(self.request.user, self.exporter)

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

    def get_success_url(self):
        return reverse("ecil:export-application:exporter-office")


class CreateExportApplicationAnotherExporterTemplateView(
    CreateExportApplicationBaseView, BackLinkMixin, TemplateView
):
    # TemplateView config
    http_method_names = ["get"]
    template_name = "ecil/export_application/another_exporter.html"
    extra_context = {
        "create_access_request_url": reverse_lazy("ecil:access_request:new"),
    }

    def get_back_link_url(self) -> str:
        return reverse("ecil:export-application:exporter")


class CreateExportApplicationAnotherExporterOfficeTemplateView(
    CreateExportApplicationBaseView, BackLinkMixin, TemplateView
):
    # TemplateView config
    http_method_names = ["get"]
    template_name = "ecil/export_application/another_exporter_office.html"
    extra_context = {
        "create_access_request_url": reverse_lazy("ecil:access_request:new"),
    }

    def get_context_data(self, **kwargs):
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
    CreateExportApplicationBaseView, TemplateView
):
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
