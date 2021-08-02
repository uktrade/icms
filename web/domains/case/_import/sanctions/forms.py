from django import forms

from web.domains.case._import.models import ImportApplicationType
from web.domains.case.forms import application_contacts
from web.domains.country.models import Country
from web.utils.commodity import get_usage_commodities, get_usage_records

from .models import SanctionsAndAdhocApplication, SanctionsAndAdhocApplicationGoods


class SanctionsAndAdhocLicenseForm(forms.ModelForm):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

        # Didn't use `get_usage_countries` for speed.
        self.fields["origin_country"].queryset = Country.objects.filter(
            country_groups__name="Sanctions and Adhoc License", is_active=True
        )

        self.fields["consignment_country"].queryset = Country.objects.filter(
            country_groups__name="Sanctions and Adhoc License Countries of shipping (consignment)",
            is_active=True,
        )


class GoodsForm(forms.ModelForm):
    quantity_amount = forms.DecimalField(label="Quantity Amount")
    value = forms.DecimalField(label="Value")

    class Meta:
        model = SanctionsAndAdhocApplicationGoods
        fields = ["commodity", "goods_description", "quantity_amount", "value"]
        widgets = {"goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20})}
        labels = {"value": "Value (GBP CIF)"}

    def __init__(self, *args, application: SanctionsAndAdhocApplication, **kwargs):
        super().__init__(*args, **kwargs)

        country_of_origin = application.origin_country

        usage_records = get_usage_records(
            ImportApplicationType.Types.SANCTION_ADHOC  # type: ignore[arg-type]
        ).filter(country=country_of_origin)

        self.fields["commodity"].queryset = get_usage_commodities(usage_records)


class GoodsSanctionsLicenceForm(forms.ModelForm):
    quantity_amount = forms.DecimalField(label="Quantity Amount")
    value = forms.DecimalField(label="Value")

    class Meta:
        model = SanctionsAndAdhocApplicationGoods
        fields = ["commodity", "goods_description", "quantity_amount", "value"]
        widgets = {"goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity"].disabled = True
