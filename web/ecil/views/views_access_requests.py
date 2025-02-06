from typing import Any

from django import forms as django_forms
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django_ratelimit import UNSAFE
from django_ratelimit.decorators import ratelimit
from jinja2.filters import do_mark_safe

from web.domains.case.services.access_request import create_export_access_request
from web.ecil.forms import forms_access_requests as forms
from web.ecil.gds.views import (
    FormStep,
    MultiStepFormSummaryView,
    MultiStepFormView,
    get_session_form_data,
    save_session_value,
)
from web.mail import emails
from web.models import Country, ExporterAccessRequest
from web.models.shared import YesNoChoices
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
            # TODO: Rename templates with -step.html suffix
            template_name="ecil/access_request/exporter_company_details-step.html",
        ),
        "company-purpose": FormStep(form_cls=forms.ExporterAccessRequestCompanyPurposeForm),
        "company-products": FormStep(form_cls=forms.ExporterAccessRequestCompanyProductsForm),
        "export-countries": FormStep(
            form_cls=forms.ExporterAccessRequestExportCountriesForm,
            template_name="ecil/access_request/exporter_countries-step.html",
        ),
    }

    template_name = "ecil/access_request/exporter_step_form.html"

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()

        if self.current_step == "export-countries":
            initial.pop("export_countries", None)

        return initial

    def form_valid(self, form: django_forms.Form | django_forms.ModelForm) -> HttpResponseRedirect:
        if self.current_step == "export-countries":
            return self.export_countries_form_valid(form)
        else:
            return super().form_valid(form)

    def get_previous_step_url(self) -> str:
        return reverse(
            "ecil:access_request:exporter_step_form", kwargs={"step": self.previous_step}
        )

    def get_next_step_url(self) -> str:
        return reverse("ecil:access_request:exporter_step_form", kwargs={"step": self.next_step})

    def export_countries_form_valid(
        self, form: forms.ExporterAccessRequestExportCountriesForm
    ) -> HttpResponseRedirect:
        cleaned_data = form.cleaned_data
        new_country = cleaned_data["export_countries"]

        saved_countries = get_session_form_data(
            self.request, self.cache_prefix(), self.current_step, "export_countries"
        )

        if saved_countries:
            saved_countries.append(new_country)
        else:
            saved_countries = [new_country]

        # Don't add (or care about) duplicates
        new_session_countries = list(set(saved_countries))
        save_session_value(
            self.request,
            self.cache_prefix(),
            self.current_step,
            "export_countries",
            new_session_countries,
        )

        # TODO: Refactor (remove) this when doing summary view.
        if self.request.POST.get("action") == "continue":
            return HttpResponseRedirect(self.get_success_url())
        else:
            return redirect(
                reverse(
                    "ecil:access_request:exporter_step_form", kwargs={"step": self.current_step}
                )
            )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if self.current_step == "export-countries":
            countries = get_session_form_data(
                self.request, self.cache_prefix(), self.current_step, "export_countries"
            )

            context["export_countries"] = countries

            if countries:
                country_qs = Country.objects.filter(pk__in=countries).order_by("name")
                if country_qs.count() > 1:
                    caption = f"You have added {country_qs.count()} countries"
                else:
                    caption = "You have added 1 country"

                rows = []
                for pk, name in country_qs.values_list("pk", "name", named=True):
                    remove_country_url = reverse(
                        "ecil:access_request:remove_export_country_form", kwargs={"country_pk": pk}
                    )
                    link = f'<a href="{remove_country_url}" class="govuk-link govuk-link--no-visited-state">Remove</a>'

                    rows.append(
                        [
                            {"text": name},
                            {"html": link, "classes": "govuk-!-text-align-right"},
                        ]
                    )

                # TODO: Use pydantic class for govuk_table_kwargs
                context["govuk_table_kwargs"] = {
                    "caption": caption,
                    "captionClasses": "govuk-table__caption--m",
                    "firstCellIsHeader": False,
                    "rows": rows,
                }

                context["summary_url"] = self.get_summary_url()

        return context

    def get_summary_url(self) -> str:
        return reverse("ecil:access_request:exporter_step_form_summary")


@method_decorator(require_exporter(check_permission=False), name="dispatch")
@method_decorator(ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE), name="post")
class ExporterAccessRequestConfirmRemoveCountryFormView(
    LoginRequiredMixin, PermissionRequiredMixin, SingleObjectMixin, FormView
):
    """View to confirm removal of export countries linked to an in progress access request."""

    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # SingleObjectMixin config
    model = Country
    pk_url_kwarg = "country_pk"
    object: Country | None = None

    # FormView config
    form_class = forms.ExporterAccessRequestRemoveExportCountryForm
    template_name = "ecil/access_request/exporter_remove_export_country_form.html"

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["country"] = self.get_object()

        return kwargs

    def form_valid(self, form):
        if form.cleaned_data["are_you_sure"] == YesNoChoices.yes:
            cache_prefix = ExporterAccessRequestMultiStepFormView.cache_prefix()
            step = "export-countries"
            field = "export_countries"

            # Saved as a str in session
            country_pk = str(form.country.pk)

            saved_countries = get_session_form_data(self.request, cache_prefix, step, field)
            if saved_countries and country_pk in saved_countries:
                saved_countries.pop(saved_countries.index(country_pk))

            save_session_value(self.request, cache_prefix, step, field, saved_countries)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_link_kwargs"] = {"text": "Back", "href": self.get_success_url()}

        return context

    def get_success_url(self) -> str:
        return reverse(
            "ecil:access_request:exporter_step_form", kwargs={"step": "export-countries"}
        )


@method_decorator(require_exporter(check_permission=False), name="dispatch")
@method_decorator(ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE), name="post")
@method_decorator(transaction.atomic, name="post")
class ExporterAccessRequestMultiStepFormSummaryView(
    LoginRequiredMixin, PermissionRequiredMixin, MultiStepFormSummaryView
):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.view_ecil_prototype]

    # MultiStepFormSummaryView config
    edit_view = ExporterAccessRequestMultiStepFormView
    form_class = forms.ExporterAccessRequestSummaryForm
    template_name = "ecil/gds_summary_list.html"
    http_method_names = ["get", "post"]

    def get_summary_cards(self, summary_items: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        card_config = [
            ("Your Details", ["request_type"]),
            (
                "Company Details",
                [
                    "organisation_name",
                    "organisation_trading_name",
                    "organisation_registered_number",
                    "organisation_address",
                ],
            ),
            (
                "Exporter Details",
                ["organisation_purpose", "organisation_products", "export_countries"],
            ),
        ]

        return [
            {
                "card": {"title": {"text": card_title}},
                "rows": [summary_items[field] for field in fields],
            }
            for card_title, fields in card_config
        ]

    def get_display_value(self, field: str, value: Any) -> str:
        match field:
            case "export_countries":
                countries = Country.objects.filter(pk__in=value)

                if countries.exists():
                    return do_mark_safe("<br>".join(countries.values_list("name", flat=True)))

                return value

            case "organisation_address" | "organisation_purpose" | "organisation_products":
                lines = value.splitlines()
                return do_mark_safe("<br>".join(lines))

            case "request_type":
                choices = dict(forms.ExporterAccessRequestTypeForm().fields["request_type"].choices)
                return choices[value]

        return super().get_display_value(field, value)

    def form_valid_save_hook(self, record: ExporterAccessRequest) -> ExporterAccessRequest:
        record = create_export_access_request(self.request, record)
        emails.send_access_requested_email(record)

        return record

    def get_edit_step_url(self, step: str) -> str:
        return reverse("ecil:access_request:exporter_step_form", kwargs={"step": step})

    def get_success_url(self) -> str:
        # TODO: Add success page url
        return reverse("workbasket")
