import datetime

from django import forms

from web.domains.case._import.ironsteel.widgets import (
    IronSteelCommodityGroupSelect,
    IronSteelCommoditySelect,
)
from web.domains.case.forms import application_contacts
from web.domains.country.models import Country

from . import models


def _get_shipping_year_selection():
    """Get year selection for Iron and Steel (Quota) applications."""
    current_year = datetime.date.today().year

    return range(current_year, current_year + 11)


class EditIronSteelForm(forms.ModelForm):
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
