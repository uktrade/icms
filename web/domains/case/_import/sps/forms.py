from django import forms

from web.domains.case.forms import application_contacts
from web.domains.file.utils import ICMSFileField
from web.forms.mixins import OptionalFormMixin
from web.models import Country
from web.utils.currency import get_euro_exchange_rate

from . import models


class SPSFormBase(forms.ModelForm):
    class Meta:
        model = models.PriorSurveillanceApplication
        fields = (
            "contact",
            "applicant_reference",
            "customs_cleared_to_uk",
            "origin_country",
            "consignment_country",
            # We are currently just showing all commodities, revisit if this becomes active again
            # NOTE: commodities seem to have these prefixes:
            # ["72", "73", "76"] -> "Iron, Steel and Aluminium"
            "commodity",
            "quantity",
            "value_gbp",
            "value_eur",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

        self.fields["customs_cleared_to_uk"].required = True
        countries = Country.util.get_non_eu_countries()
        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries

        exchange_rate = get_euro_exchange_rate()
        self.fields["value_eur"].disabled = True
        self.fields["value_eur"].required = False
        self.fields["value_eur"].help_text = (
            f"Converted at a rate of 1 GBP to {exchange_rate} EUR, rounded up"
            f" to the nearest EUR."
        )


class EditSPSForm(OptionalFormMixin, SPSFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitSPSForm(SPSFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """

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
