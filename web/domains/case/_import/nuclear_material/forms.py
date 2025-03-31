import datetime as dt
import re
from typing import Any

from django import forms
from django.db.models import QuerySet

from web.domains.case.forms import application_contacts
from web.domains.commodity.forms import COMMODITY_HELP_TEXT
from web.forms.fields import JqueryDateField
from web.forms.mixins import OptionalFormMixin
from web.models import Commodity, Country, Unit
from web.utils.commodity import get_active_commodities

from .models import NuclearMaterialApplication, NuclearMaterialApplicationGoods


class NuclearMaterialApplicationFormBase(forms.ModelForm):
    shipment_start_date = JqueryDateField(
        label="Date of shipment",
        required=True,
    )
    shipment_end_date = JqueryDateField(label="Date of last shipment", required=False)

    class Meta:
        model = NuclearMaterialApplication
        fields = (
            "contact",
            "applicant_reference",
            "origin_country",
            "consignment_country",
            "nature_of_business",
            "consignor_name",
            "consignor_address",
            "end_user_name",
            "end_user_address",
            "intended_use_of_shipment",
            "licence_type",
            "shipment_start_date",
            "shipment_end_date",
            "security_team_contact_information",
        )

        widgets = {
            "nature_of_business": forms.Textarea(attrs={"rows": 6}),
            "consignor_address": forms.Textarea(attrs={"rows": 6}),
            "end_user_address": forms.Textarea(attrs={"rows": 6}),
        }

        labels = {
            "applicant_reference": "Applicant's reference",
            "origin_country": "Country of manufacture (origin)",
            "consignment_country": "Country of shipment (consignment)",
            "intended_use_of_shipment": "Intended end use of shipment",
        }
        help_texts = {
            "consignment_country": (
                "Country from which the goods will be physically consigned or despatched."
            ),
            "nature_of_business": (
                "Please state exactly what aspect of your business has led you to require an import licence for nuclear materials."
            ),
            "consignor_name": "This is the overseas organisation that has sent the consignment of nuclear material to the UK.",
            "end_user_name": (
                "The applicant may not always be the end user. Where the nuclear material imported is to be forwarded by "
                "the applicant, appropriate details are to be provided."
            ),
            "intended_use_of_shipment": "The end use of a shipment of nuclear materials may be a significant factor in considering an application.",
            "licence_type": (
                "An Import Licence may be issued for one shipment or, if moving large quantities of one type of nuclear material, "
                "may be valid for a series of movements lasting up to one year."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

        all_countries = Country.util.get_all_countries()
        self.fields["origin_country"].queryset = all_countries
        self.fields["consignment_country"].queryset = all_countries
        self.fields["licence_type"].choices = [("", "---------")] + list(
            self.fields["licence_type"].choices
        )

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        shipment_start_date = cleaned_data.get("shipment_start_date")
        shipment_end_date = cleaned_data.get("shipment_end_date")
        licence_type = cleaned_data.get("licence_type")
        today = dt.date.today()

        if not shipment_start_date or shipment_start_date < today:
            self.add_error("shipment_start_date", "Date of shipment cannot be in the past.")

        if licence_type == self.Meta.model.LicenceType.OPEN:
            if not shipment_end_date:
                self.add_error(
                    "shipment_end_date",
                    "Date of last shipment must be provided for an open licence type.",
                )
            elif shipment_end_date <= shipment_start_date:
                self.add_error(
                    "shipment_end_date",
                    "Date of last shipment must be after date of first shipment.",
                )
        else:
            cleaned_data["shipment_end_date"] = None

        return cleaned_data


class EditNuclearMaterialApplicationForm(OptionalFormMixin, NuclearMaterialApplicationFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitNuclearMaterialApplicationForm(NuclearMaterialApplicationFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """


class GoodsForm(forms.ModelForm):
    class Meta:
        model = NuclearMaterialApplicationGoods
        fields = [
            "commodity",
            "goods_description",
            "quantity_amount",
            "quantity_unit",
            "unlimited_quantity",
        ]
        widgets = {
            "goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20}),
            "quantity_amount": forms.NumberInput(attrs={"step": 1}),
        }

        labels = {"goods_description": "Goods description (including UN number)"}

        help_texts = {
            "commodity": COMMODITY_HELP_TEXT,
            "goods_description": "A brief description of the material, including the relevant UN number and packages/seals used for the transport.",
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["commodity"].queryset = nuclear_material_available_commodities()
        self.fields["quantity_unit"].queryset = nuclear_material_available_units()

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity_amount")
        unlimited_quantity = cleaned_data.get("unlimited_quantity")

        if not quantity and not unlimited_quantity:
            self.add_error(
                "quantity_amount",
                "You must enter either a quantity or select unlimited quantity",
            )

        if unlimited_quantity:
            cleaned_data["quantity_amount"] = None

        return cleaned_data

    def clean_goods_description(self):
        description = self.cleaned_data["goods_description"]
        return re.sub(r"\s+", " ", description)


class GoodsNuclearMaterialApplicationForm(forms.ModelForm):
    """Form used by ILB to edit goods linked to a nuclear material application."""

    class Meta:
        model = NuclearMaterialApplicationGoods
        fields = [
            "commodity",
            "goods_description",
            "quantity_amount",
            "quantity_unit",
        ]
        widgets = {"goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20})}
        help_texts = {"commodity": COMMODITY_HELP_TEXT}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity"].disabled = True
        self.fields["quantity_unit"].queryset = nuclear_material_available_units()

        if self.instance.unlimited_quantity:
            self.fields["quantity_amount"].required = False
            self.fields["quantity_amount"].widget = forms.NumberInput(
                attrs={"placeholder": "Unlimited"}
            )
            self.fields["quantity_amount"].disabled = True

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        unlimited_quantity = self.instance.unlimited_quantity

        if unlimited_quantity:
            cleaned_data["quantity_amount"] = None

        return cleaned_data

    def clean_goods_description(self):
        description = self.cleaned_data["goods_description"]
        return re.sub(r"\s+", " ", description)


def nuclear_material_available_commodities() -> QuerySet[Commodity]:
    return get_active_commodities(
        Commodity.objects.filter(commoditygroup__group_code__in=["2612", "2844"])
    ).order_by("commodity_code")


def nuclear_material_available_units() -> QuerySet[Unit]:
    return Unit.objects.filter(hmrc_code__in=["23", "21", "74", "76", "116"]).order_by(
        "description"
    )
