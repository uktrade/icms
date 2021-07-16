from django import forms

from web.domains.country.models import Country
from web.domains.file.utils import ICMSFileField
from web.domains.user.models import User
from web.utils.currency import get_euro_exchange_rate

from . import models


class EditSPSForm(forms.ModelForm):
    class Meta:
        model = models.PriorSurveillanceApplication
        fields = (
            "contact",
            "applicant_reference",
            "customs_cleared_to_uk",
            "origin_country",
            "consignment_country",
            # TODO: Revisit when doing ICMSLST-853
            # We are currently just showing all commodities
            "commodity",
            "quantity",
            "value_gbp",
            "value_eur",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: ICMSLST-425 filter users here correctly (users with access to the importer)
        self.fields["contact"].queryset = User.objects.all()

        self.fields["customs_cleared_to_uk"].required = True

        countries = Country.objects.filter(country_groups__name="Non EU Single Countries")
        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries

        exchange_rate = get_euro_exchange_rate()
        self.fields["value_eur"].disabled = True
        self.fields["value_eur"].required = False
        self.fields["value_eur"].help_text = (
            f"Converted at a rate of 1 GBP to {exchange_rate} EUR, rounded up"
            f" to the nearest EUR."
        )

    def clean_quantity(self) -> int:
        quantity: int = self.cleaned_data["quantity"]

        if quantity < 2500:
            raise forms.ValidationError("Amounts below 2500 Kilos do not need a licence.")

        return quantity


class AddContractDocumentForm(forms.ModelForm):
    document = ICMSFileField(required=True)

    class Meta:
        model = models.PriorSurveillanceContractFile
        fields = ("file_type",)


class EditContractDocumentForm(forms.ModelForm):
    class Meta:
        model = models.PriorSurveillanceContractFile

        fields = ("file_type",)


class ResponsePrepGoodsForm(forms.ModelForm):
    class Meta:
        model = models.PriorSurveillanceApplication
        fields = ("quantity",)
