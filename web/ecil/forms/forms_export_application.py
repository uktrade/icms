from typing import Any, Literal

from guardian.shortcuts import get_objects_for_user

from web.ecil.gds import forms as gds_forms
from web.ecil.types import EXPORT_APPLICATION
from web.models import Country, Exporter, User
from web.models.shared import YesNoChoices
from web.permissions import Perms


class ExportApplicationTypeForm(gds_forms.GDSForm):
    app_type = gds_forms.GovUKRadioInputField(
        label="Which certificate are you applying for?",
        error_messages={
            "required": "Select the certificate you are applying for.",
        },
        choices=[
            ("cfs", "Certificate of Free Sale (CFS)"),
            ("com", "Certificate of Manufacture (CoM)"),
            ("gmp", "Certificate of Good Manufacturing Practice (CGMP)"),
        ],
        choice_hints={
            "cfs": "Products which meet UK standards that fall under Department for Business and Trade regulation.",
            "com": "Pesticides that are solely for use in overseas markets and will not be placed on the UK market.",
            "gmp": "Cosmetic products which meet UK good manufacturing practice standards. For use in China only.",
        },
        choice_classes="govuk-!-font-weight-bold",
        gds_field_kwargs={
            "fieldset": {"legend": {"isPageHeading": True, "classes": "govuk-fieldset__legend--l"}}
        },
    )


class ExportApplicationExporterForm(gds_forms.GDSForm):
    exporter = gds_forms.GovUKRadioInputField(
        label="Which company do you want an export certificate for?",
        error_messages={"required": "Select the company you want an export certificate for."},
        gds_field_kwargs={
            "fieldset": {"legend": {"isPageHeading": True, "classes": "govuk-fieldset__legend--l"}}
        },
    )

    def clean_exporter(self) -> Literal["none-of-these"] | int:
        exporter_pk = self.cleaned_data["exporter"]

        if exporter_pk == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            return exporter_pk

        return self.exporters.get(pk=exporter_pk).pk

    def __init__(self, *args: Any, user: User, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

        # TODO: This should be refactored to a reusable function
        # Main exporters the user can edit or is an agent of.
        self.exporters = get_objects_for_user(
            user,
            [Perms.obj.exporter.edit, Perms.obj.exporter.is_agent],
            Exporter.objects.filter(is_active=True, main_exporter__isnull=True),
            any_perm=True,
        )

        exporter_list = [(c.pk, c.name) for c in self.exporters]
        exporter_list.append((gds_forms.GovUKRadioInputField.NONE_OF_THESE, "Another company"))
        self.fields["exporter"].choices = exporter_list


class ExportApplicationExportCountriesForm(gds_forms.GDSForm):
    # Can't use a ModelForm here as "countries" is a ManyToMany model field.
    # There are no GDS components that can render a select multiple form field.
    # Therefore, it's cleaner to create a GDSForm and save the data in the view.
    countries = gds_forms.GovUKSelectField(
        label="Where do you want to export products to?",
        help_text=(
            "Enter a country or territory and select from the results."
            " You can add up to 40 countries or territories."
        ),
        choices=[],
        gds_field_kwargs={"label": {"isPageHeading": True, "classes": "govuk-label--l"}},
        error_messages={"required": "Select a country or territory you want to export to"},
    )

    def __init__(self, *args: Any, instance: EXPORT_APPLICATION, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.instance = instance
        self.selected_countries = self.instance.countries.all()

        countries = [(None, "")] + list(Country.app.get_cfs_countries().values_list("id", "name"))
        self.fields["countries"].choices = countries

    def clean_countries(self) -> Country | None:
        if country_pk := self.cleaned_data.get("countries"):
            return Country.app.get_cfs_countries().get(pk=country_pk)

        return None

    def clean(self) -> None:
        cleaned_data = super().clean()

        if (
            self.selected_countries
            and cleaned_data.get("countries")
            and len(self.selected_countries) >= 40
        ):
            self.add_error("countries", "You can only add up to 40 countries or territories")

        return cleaned_data


class ExportApplicationRemoveExportCountryForm(gds_forms.GDSForm):
    are_you_sure = gds_forms.GovUKRadioInputField(
        choices=YesNoChoices.choices,
        gds_field_kwargs={
            "fieldset": {"legend": {"isPageHeading": True, "classes": "govuk-fieldset__legend--l"}}
        },
        error_messages={"required": "Select yes or no"},
    )

    def __init__(self, *args: Any, country: Country, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.country = country
        self.fields["are_you_sure"].label = f"Are you sure you want to remove {country}?"
