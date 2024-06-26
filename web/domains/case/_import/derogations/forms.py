from typing import TYPE_CHECKING, Any

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.forms.fields import JqueryDateField
from web.forms.mixins import OptionalFormMixin
from web.models import Country, ImportApplicationType
from web.utils.commodity import get_usage_records

from .models import DerogationsApplication, DerogationsChecklist
from .widgets import DerogationCommoditySelect, DerogationCountryOfOriginSelect

if TYPE_CHECKING:
    from decimal import Decimal

    from web.models import Commodity


class DerogationsFormBase(forms.ModelForm):
    contract_sign_date = JqueryDateField(required=True, label="Contract Sign Date")
    contract_completion_date = JqueryDateField(required=True, label="Contract Completion Date")

    class Meta:
        model = DerogationsApplication
        fields = (
            "contact",
            "applicant_reference",
            "origin_country",
            "consignment_country",
            "contract_sign_date",
            "contract_completion_date",
            "explanation",
            "commodity",
            "goods_description",
            "quantity",
            "unit",
            "value",
            # Further details fields (for Syria)
            "entity_consulted_name",
            "activity_benefit_anyone",
            "purpose_of_request",
            "civilian_purpose_details",
        )
        widgets = {
            "explanation": forms.Textarea(attrs={"cols": 50, "rows": 3}),
            "origin_country": DerogationCountryOfOriginSelect,
            "commodity": DerogationCommoditySelect,
            "civilian_purpose_details": forms.Textarea(attrs={"cols": 50, "rows": 3}),
        }

        help_texts = {
            "origin_country": (
                "Select the country that the goods originate from. Please consult the"
                " Guidance or relevant Notice to Importers to ensure that a derogation"
                " is applicable and the terms of that derogation for the goods you wish"
                " to import."
            ),
            "consignment_country": (
                "Country from which the goods will be physically consigned or despatched."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)
        non_eu_countries = Country.util.get_non_eu_countries()
        self.fields["consignment_country"].queryset = non_eu_countries


class EditDerogationsForm(OptionalFormMixin, DerogationsFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitDerogationsForm(DerogationsFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """

    def clean(self):
        """Check if the quantity exceeds the maximum_allocation if set."""
        cleaned_data = super().clean()

        if not self.is_valid():
            return cleaned_data

        origin_country: Country = cleaned_data["origin_country"]
        commodity: "Commodity" = cleaned_data["commodity"]
        quantity: "Decimal" = cleaned_data["quantity"]

        usage = get_usage_records(ImportApplicationType.Types.DEROGATION)
        usage = usage.filter(
            country=origin_country,
            commodity_group__commodities__in=[commodity],
            maximum_allocation__isnull=False,
        ).distinct()

        for record in usage:
            if quantity > record.maximum_allocation:
                self.add_error(
                    "quantity",
                    f"Quantity exceeds maximum allocation (max: {record.maximum_allocation})",
                )
                break

        self._clean_syria_further_details(cleaned_data)

        self._check_valid_countries(cleaned_data)

        return cleaned_data

    def _clean_syria_further_details(self, cleaned_data: dict[str, Any]) -> None:
        syria: Country = Country.objects.get(name="Syria")
        origin_country: Country = cleaned_data["origin_country"]
        consignment_country: Country = cleaned_data["consignment_country"]

        if syria not in (origin_country, consignment_country):
            return

        fields = ("entity_consulted_name", "activity_benefit_anyone", "purpose_of_request")

        for f in fields:
            val = cleaned_data.get(f)

            if not val:
                self.add_error(f, "You must enter this item")

        purpose_of_request = cleaned_data.get("purpose_of_request")
        civilian_purpose_details = cleaned_data.get("civilian_purpose_details")
        is_other_civ_purpose = (
            purpose_of_request == DerogationsApplication.SyrianRequestPurpose.OTHER_CIV_PURPOSE
        )

        if is_other_civ_purpose and not civilian_purpose_details:
            self.add_error("civilian_purpose_details", "You must enter this item")

    def _check_valid_countries(self, cleaned_data: dict[str, Any]) -> None:
        """Check one of origin_country & consignment_country is set to a valid country."""

        valid_countries = ("Iran", "Russian Federation", "Somalia", "Syria")
        origin_country: Country = cleaned_data["origin_country"]
        consignment_country: Country = cleaned_data["consignment_country"]

        if (
            origin_country.name not in valid_countries
            and consignment_country.name not in valid_countries
        ):
            self.add_error(
                "consignment_country",
                "The country of origin or country of consignment must be one of"
                " Iran, Russian Federation, Somalia or Syria",
            )


class DerogationsChecklistForm(ChecklistBaseForm):
    class Meta:
        model = DerogationsChecklist

        fields = ("supporting_document_received",) + ChecklistBaseForm.Meta.fields


class DerogationsChecklistOptionalForm(DerogationsChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class DerogationsSyriaChecklistForm(DerogationsChecklistForm):
    class Meta:
        model = DerogationsChecklist

        fields = DerogationsChecklistForm.Meta.fields + (
            "sncorf_consulted",
            "sncorf_response_within_30_days",
            "beneficiaries_not_on_list",
            "request_purpose_confirmed",
        )


class DerogationsSyriaChecklistOptionalForm(DerogationsSyriaChecklistForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class GoodsDerogationsLicenceForm(forms.ModelForm):
    quantity = forms.DecimalField()
    unit = forms.ChoiceField(
        label="Unit",
        choices=[(x, x) for x in ["kilos"]],
    )

    value = forms.CharField(
        label="Value (GBP)",
        required=True,
    )

    class Meta:
        model = DerogationsApplication
        fields = ("commodity", "goods_description", "quantity", "unit", "value")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity"].widget.attrs["readonly"] = True
