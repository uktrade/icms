import datetime as dt
import re

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case._import.ironsteel.widgets import (
    IronSteelCommodityGroupSelect,
    IronSteelCommoditySelect,
)
from web.domains.case.forms import application_contacts
from web.domains.file.utils import ICMSFileField
from web.forms.mixins import OptionalFormMixin
from web.models import Country

from . import models


def _get_shipping_year_selection():
    """Get year selection for Iron and Steel (Quota) applications."""
    current_year = dt.date.today().year

    return range(current_year, current_year + 11)


class IronSteelFormBase(forms.ModelForm):
    class Meta:
        model = models.IronSteelApplication
        fields = (
            "contact",
            "applicant_reference",
            "goods_cleared",
            "shipping_year",
            "origin_country",
            "consignment_country",
            "category_commodity_group",
            "commodity",
            "goods_description",
            "quantity",
        )

        widgets = {
            "shipping_year": forms.Select(choices=[(x, x) for x in _get_shipping_year_selection()]),
            "category_commodity_group": IronSteelCommodityGroupSelect,
            "commodity": IronSteelCommoditySelect,
            "quantity": forms.NumberInput(attrs={"step": 1}),
        }

        help_texts = {
            "origin_country": (
                "Select the country that the goods originate from."
                " Imports from Kazahkstan are subject to EU quotas."
                " Please consult the guidance to check what can be imported this year."
            ),
            "consignment_country": (
                "Select the country that the goods will be consigned/dispatched from."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

        self.fields["goods_cleared"].required = True
        self.fields["goods_cleared"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]

        self.fields["origin_country"].queryset = Country.objects.filter(
            country_groups__name="Iron and Steel (Quota) COOs", is_active=True
        )

        self.fields["consignment_country"].queryset = Country.objects.filter(
            country_groups__name="Iron and Steel (Quota) COCs", is_active=True
        )


class EditIronSteelForm(OptionalFormMixin, IronSteelFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitIronSteelForm(IronSteelFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """


class CertificateFormBase(forms.ModelForm):
    class Meta:
        model = models.IronSteelCertificateFile
        fields = ("reference", "total_qty", "requested_qty")

    def clean_reference(self):
        ref = self.cleaned_data["reference"]

        if not ref.startswith("KZ"):
            raise forms.ValidationError(
                "Prefix of certificate reference is incorrect. Please ensure"
                " you have entered a reference for a certificate that applies"
                " to the selected Country of Origin."
            )

        # four characters followed by eight digits, e.g. KZGB12345678
        if not re.match("[A-Z]{4}\\d{8}$", ref):
            raise forms.ValidationError("Entry is in an incorrect format.")

        return ref

    def clean(self):
        cleaned = super().clean()

        if not self.is_valid():
            return cleaned

        total_qty = cleaned["total_qty"]
        requested_qty = cleaned["requested_qty"]

        if requested_qty > total_qty:
            self.add_error(
                "requested_qty",
                "Requested quantity cannot exceed maximum quantity per certificate.",
            )


class AddCertificateForm(CertificateFormBase):
    document = ICMSFileField(required=True)


class EditCertificateForm(CertificateFormBase):
    pass


class IronSteelChecklistForm(ChecklistBaseForm):
    class Meta:
        model = models.IronSteelChecklist
        fields = ("licence_category",) + ChecklistBaseForm.Meta.fields


class IronSteelChecklistOptionalForm(IronSteelChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class ResponsePrepGoodsForm(forms.ModelForm):
    class Meta:
        model = models.IronSteelApplication
        fields = ("goods_description", "quantity")
        widgets = {"quantity": forms.NumberInput(attrs={"step": 1})}


class ResponsePrepCertificateForm(forms.ModelForm):
    class Meta:
        model = models.IronSteelCertificateFile
        fields = ("requested_qty",)
        widgets = {"requested_qty": forms.NumberInput(attrs={"step": 1})}
