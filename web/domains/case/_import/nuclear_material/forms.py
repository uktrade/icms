import re
from typing import Any

from django import forms
from django.db.models import QuerySet

from web.domains.case.forms import application_contacts
from web.domains.commodity.forms import COMMODITY_HELP_TEXT
from web.forms.mixins import OptionalFormMixin
from web.models import Commodity, Country, Unit
from web.utils.commodity import get_active_commodities

from .models import NuclearMaterialApplication, NuclearMaterialApplicationGoods


class NuclearMaterialApplicationFormBase(forms.ModelForm):
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
            "dates_of_shipment",
            "security_team_contact_information",
            "licence_type",
        )

        widgets = {
            "nature_of_business": forms.Textarea(attrs={"rows": 6}),
            "consignor_address": forms.Textarea(attrs={"rows": 6}),
            "end_user_address": forms.Textarea(attrs={"rows": 6}),
        }

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

        all_countries = Country.util.get_all_countries()
        self.fields["origin_country"].queryset = all_countries
        self.fields["consignment_country"].queryset = all_countries
        self.fields["licence_type"].choices = [("", "---------")] + list(
            self.fields["licence_type"].choices
        )


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
        fields = ["commodity", "goods_description", "quantity_amount", "quantity_unit"]
        widgets = {
            "goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20}),
            "quantity_amount": forms.NumberInput(attrs={"step": 1}),
        }
        help_texts = {"commodity": COMMODITY_HELP_TEXT}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["commodity"].queryset = nuclear_material_available_commodities()
        self.fields["quantity_unit"].queryset = nuclear_material_available_units()

    def clean_goods_description(self):
        description = self.cleaned_data["goods_description"]
        return re.sub(r"\s+", " ", description)


class GoodsNuclearMaterialApplicationForm(forms.ModelForm):
    """Form used by ILB to edit goods linked to a nuclear material application."""

    class Meta:
        model = NuclearMaterialApplicationGoods
        fields = ["commodity", "goods_description", "quantity_amount", "quantity_unit"]
        widgets = {"goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20})}
        help_texts = {"commodity": COMMODITY_HELP_TEXT}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity"].disabled = True

    def clean_goods_description(self):
        description = self.cleaned_data["goods_description"]
        return re.sub(r"\s+", " ", description)


def nuclear_material_available_commodities() -> QuerySet[Commodity]:
    return get_active_commodities(
        Commodity.objects.filter(commoditygroup__group_code__in=["2612", "2844"])
    ).order_by("commodity_code")


def nuclear_material_available_units() -> QuerySet[Unit]:
    return Unit.objects.filter(hmrc_code__in=["23", "21", "74", "76"]).order_by("description")
