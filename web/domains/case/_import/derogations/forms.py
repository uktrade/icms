from typing import TYPE_CHECKING, Any

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case._import.models import ImportApplicationType
from web.domains.case.forms import application_contacts
from web.domains.country.models import Country
from web.forms.widgets import DateInput
from web.utils.commodity import get_usage_records

from .models import DerogationsApplication, DerogationsChecklist
from .widgets import DerogationCommoditySelect, DerogationCountryOfOriginSelect

if TYPE_CHECKING:
    from decimal import Decimal

    from web.domains.commodity.models import Commodity


class DerogationsForm(forms.ModelForm):
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
            "contract_sign_date": DateInput,
            "contract_completion_date": DateInput,
            "explanation": forms.Textarea(attrs={"cols": 50, "rows": 3}),
            "origin_country": DerogationCountryOfOriginSelect,
            "commodity": DerogationCommoditySelect,
            "civilian_purpose_details": forms.Textarea(attrs={"cols": 50, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

        non_eu_countries = Country.objects.filter(country_groups__name="Non EU Single Countries")
        self.fields["consignment_country"].queryset = non_eu_countries

    def clean(self):
        """Check if the quantity exceeds the maximum_allocation if set."""
        cleaned_data = super().clean()

        if not self.is_valid():
            return cleaned_data

        origin_country: Country = cleaned_data["origin_country"]
        commodity: "Commodity" = cleaned_data["commodity"]
        quantity: "Decimal" = cleaned_data["quantity"]

        usage = get_usage_records(ImportApplicationType.Types.DEROGATION)  # type: ignore[arg-type]
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


class GoodsDerogationsLicenceForm(forms.ModelForm):
    quantity = forms.DecimalField()
    unit = forms.ChoiceField(
        label="Unit",
        choices=[(x, x) for x in ["kilos"]],
    )

    value = forms.CharField(
        label="Value (euro CIF)",
        required=True,
    )

    class Meta:
        model = DerogationsApplication
        fields = ("commodity", "goods_description", "quantity", "unit", "value")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity"].widget.attrs["readonly"] = True
