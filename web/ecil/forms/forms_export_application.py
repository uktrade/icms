from typing import Any

from web.ecil.gds import forms as gds_forms
from web.ecil.types import EXPORT_APPLICATION
from web.models import Country
from web.models.shared import YesNoChoices


class ExportApplicationExportCountriesForm(gds_forms.GDSForm):
    # Can't use a ModelForm here as "countries" is a ManyToMany model field.
    # There are no GDS components that can render a select multiple form field.
    # Therefore, it's cleaner to create a GDSForm and save the data in the view.
    countries = gds_forms.GovUKSelectField(
        label="Where do you want to export products to?",
        help_text=(
            "Enter a country or territory and select from the results."
            " You can add up to 40 countries or territories."
            " You can change these later if you need to."
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
