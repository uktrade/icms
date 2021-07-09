from django import forms

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
            # TODO: Revisit this when fleshing out ICMSLST-749 (Commodity spike)
            # We are currently just showing all commodities
            "commodity",
            "quantity",
            "value_gbp",
            "value_euro",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: ICMSLST-425 filter users here correctly (users with access to the importer)
        self.fields["contact"].queryset = User.objects.all()

        exchange_rate = get_euro_exchange_rate()
        self.fields["value_euro"].disabled = True
        self.fields["value_euro"].required = False
        self.fields["value_euro"].help_text = (
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
