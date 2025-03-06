from typing import Any
from urllib import parse

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import Resolver404, ResolverMatch, resolve, reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from web.domains.case.services import case_progress
from web.ecil.forms import forms_export_application as forms
from web.ecil.gds import component_serializers as serializers
from web.ecil.types import EXPORT_APPLICATION
from web.flow.models import ProcessTypes
from web.models import Country, User
from web.models.shared import YesNoChoices
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest


class AnotherExportApplicationContactTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

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
                caption = f"You have added {country_qs.count()} countries"
            else:
                caption = "You have added 1 country"

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
