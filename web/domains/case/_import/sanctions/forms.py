from django import forms

from web.domains.case.forms import application_contacts
from web.domains.country.models import Country

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

        countries = Country.objects.filter(country_groups__name="Sanctions and Adhoc License")
        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries


class GoodsForm(forms.ModelForm):
    commodity_code = forms.ChoiceField(
        label="Commodity Code",
        help_text="""
            It is the responsibility of the applicant to ensure that the commodity code in this box
            is correct. If you are unsure of the correct commodity code, consult the HM Revenue and
            Customs Integrated Tariff Book, Volume 2, which is available from the Stationery Office.
            If you are still in doubt, contact the Classification Advisory Service on (01702) 366077.
        """,
        choices=[(x, x) for x in [None, "2850009000", "2850002070", "2828282828", "2801010101"]],
    )
    quantity_amount = forms.DecimalField(label="Quantity Amount")
    value = forms.DecimalField(label="Value")

    class Meta:
        model = SanctionsAndAdhocApplicationGoods
        fields = ["commodity_code", "goods_description", "quantity_amount", "value"]
        widgets = {"goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20})}
        labels = {"value": "Value (GBP CIF)"}


class GoodsSanctionsLicenceForm(forms.ModelForm):
    quantity_amount = forms.DecimalField(label="Quantity Amount")
    value = forms.DecimalField(label="Value")

    class Meta:
        model = SanctionsAndAdhocApplicationGoods
        fields = ["commodity_code", "goods_description", "quantity_amount", "value"]
        widgets = {"goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity_code"].widget.attrs["readonly"] = True
