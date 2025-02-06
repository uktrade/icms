from typing import Any

from web.ecil.gds import forms as gds_forms
from web.models import Country, ExporterAccessRequest
from web.models.shared import YesNoChoices


class ExporterAccessRequestTypeForm(gds_forms.GDSModelForm):
    # Use a custom field as the choice labels are wrong on the model
    request_type = gds_forms.GovUKRadioInputField(
        label="Are you an exporter or an agent?",
        choices=(
            (ExporterAccessRequest.MAIN_EXPORTER_ACCESS, "Exporter"),
            (ExporterAccessRequest.AGENT_ACCESS, "Agent"),
        ),
        choice_hints={
            ExporterAccessRequest.MAIN_EXPORTER_ACCESS: "You are a company director or employee",
            ExporterAccessRequest.AGENT_ACCESS: (
                "You are acting on behalf of a company or individual that already has a"
                " registered account"
            ),
        },
        error_messages={"required": "Select if you are an exporter or an agent"},
        gds_field_kwargs={
            "fieldset": {"legend": {"isPageHeading": True, "classes": "govuk-fieldset__legend--l"}}
        },
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ExporterAccessRequest
        fields = ["request_type"]


class ExporterAccessRequestCompanyDetailsForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ExporterAccessRequest
        fields = [
            "organisation_name",
            "organisation_trading_name",
            "organisation_registered_number",
            "organisation_address",
        ]

        labels = {
            "organisation_name": "Company name",
            "organisation_trading_name": "Trading name (Optional)",
            "organisation_registered_number": "Company number (Optional)",
            "organisation_address": "Address",
        }

        error_messages = {
            "organisation_name": {"required": "Enter company name"},
            "organisation_address": {"required": "Enter an address, including a postcode"},
        }

        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={
                "organisation_registered_number": {"classes": "govuk-!-width-one-third"}
            }
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Only way to remove the help text defined on the ExporterAccessRequest model
        self.fields["organisation_registered_number"].help_text = None


class ExporterAccessRequestCompanyPurposeForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ExporterAccessRequest
        fields = [
            "organisation_purpose",
        ]
        error_messages = {"organisation_purpose": {"required": "Enter what the company does"}}

        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={
                "organisation_purpose": {
                    "label": {"isPageHeading": True, "classes": "govuk-label--l"}
                }
            }
        )


class ExporterAccessRequestCompanyProductsForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ExporterAccessRequest
        fields = [
            "organisation_products",
        ]

        labels = {"organisation_products": "What type of products do you want to export?"}
        help_texts = {
            "organisation_products": (
                "Give an overview of the products you want to export. For example, cosmetics."
            )
        }

        error_messages = {
            "organisation_products": {"required": "Enter the type of products you want to export"}
        }

        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={
                "organisation_products": {
                    "label": {"isPageHeading": True, "classes": "govuk-label--l"}
                }
            }
        )


class ExporterAccessRequestExportCountriesForm(gds_forms.GDSModelForm):
    export_countries = gds_forms.GovUKSelectField(
        label="What countries do you want to export to?",
        help_text=(
            "Start typing a country to add it. You can add up to 40 countries."
            " You are not limited to these countries and you can change them later if you need to."
        ),
        choices=[],
        gds_field_kwargs={"label": {"isPageHeading": True, "classes": "govuk-label--l"}},
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        countries = [(None, "")] + list(Country.util.get_all_countries().values_list("id", "name"))
        self.fields["export_countries"].choices = countries

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ExporterAccessRequest
        fields = [
            "export_countries",
        ]


class ExporterAccessRequestRemoveExportCountryForm(gds_forms.GDSForm):
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


# TODO: Revisit in ECIL-606 (Change to ModelForm)
class ExporterAccessRequestSummaryForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ExporterAccessRequest
        fields = [
            "request_type",
            "organisation_name",
            "organisation_trading_name",
            "organisation_registered_number",
            "organisation_address",
            "organisation_purpose",
            "organisation_products",
            "export_countries",
        ]

        labels = {
            "request_type": "Are you an exporter or an agent?",
            "organisation_name": "Company name",
            "organisation_trading_name": "Trading name",
            "organisation_registered_number": "Company number",
            "organisation_address": "Address",
            "organisation_products": "What type of products do you want to export?",
            "export_countries": "What countries do you want to export to?",
        }
