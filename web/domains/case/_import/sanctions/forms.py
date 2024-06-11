from typing import Any

from django import forms

from web.domains.case.forms import application_contacts
from web.forms.mixins import OptionalFormMixin
from web.models import Country, ImportApplicationType
from web.utils.commodity import get_usage_commodities, get_usage_records

from .models import SanctionsAndAdhocApplication, SanctionsAndAdhocApplicationGoods


class SanctionsAndAdhocLicenceFormBase(forms.ModelForm):
    exporter_name = forms.CharField(
        label="Exporter Name",
        required=False,
    )
    exporter_address = forms.CharField(
        label="Exporter Address",
        required=False,
    )

    class Meta:
        model = SanctionsAndAdhocApplication
        fields = (
            "contact",
            "applicant_reference",
            "origin_country",
            "consignment_country",
            "exporter_name",
            "exporter_address",
        )
        labels = {
            "origin_country": "Country of manufacture (origin)",
            "consignment_country": "Country of shipment (consignment)",
        }
        help_texts = {
            "consignment_country": (
                "Country from which the goods will be physically consigned or despatched."
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

        sanction_countries = Country.app.get_sanctions_coo_and_coc_countries()
        self.fields["origin_country"].queryset = sanction_countries
        self.fields["consignment_country"].queryset = sanction_countries

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        origin = cleaned_data.get("origin_country")
        consignment = cleaned_data.get("consignment_country")

        if origin and consignment:
            sanctioned = Country.app.get_sanctions_countries().values_list("pk", flat=True)
            # One or both countries should be sanctioned
            if origin.pk not in sanctioned and consignment.pk not in sanctioned:
                # values_list doesn't support negative indexing so create a list.
                names = list(
                    Country.app.get_sanctions_countries()
                    .order_by("name")
                    .values_list("name", flat=True)
                )
                error = f"The country of manufacture or country of shipment must be one of {', '.join(names[:-1])} or {names[-1]}"
                self.add_error("origin_country", error)

        return cleaned_data


class EditSanctionsAndAdhocLicenceForm(OptionalFormMixin, SanctionsAndAdhocLicenceFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitSanctionsAndAdhocLicenceForm(SanctionsAndAdhocLicenceFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """


class GoodsForm(forms.ModelForm):
    class Meta:
        model = SanctionsAndAdhocApplicationGoods
        fields = ["commodity", "goods_description", "quantity_amount", "value"]
        widgets = {
            "goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20}),
            "quantity_amount": forms.NumberInput(attrs={"step": 1}),
            "value": forms.NumberInput(attrs={"step": 1}),
        }

    def __init__(
        self, *args: Any, application: SanctionsAndAdhocApplication, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        sanctioned_countries = Country.app.get_sanctions_countries()

        countries_to_search = []
        if application.origin_country in sanctioned_countries:
            countries_to_search.append(application.origin_country)

        if application.consignment_country in sanctioned_countries:
            countries_to_search.append(application.consignment_country)

        usage_records = get_usage_records(ImportApplicationType.Types.SANCTION_ADHOC).filter(
            country__in=countries_to_search
        )

        self.fields["commodity"].queryset = get_usage_commodities(usage_records)


class GoodsSanctionsLicenceForm(forms.ModelForm):
    class Meta:
        model = SanctionsAndAdhocApplicationGoods
        fields = ["commodity", "goods_description", "quantity_amount", "value"]
        widgets = {"goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity"].disabled = True
