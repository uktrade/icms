from web.ecil.gds import forms as gds_forms
from web.models import ExporterAccessRequest


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
            "organisation_address": {"required": "Enter an address, including a postcode."},
        }

        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={
                "organisation_registered_number": {"classes": "govuk-!-width-one-third"}
            }
        )

    def __init__(self, *args, **kwargs):
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
