import datetime

from django import forms

from web.domains.country.models import Country
from web.domains.user.models import User

from . import models
from .widgets import TextilesCategoryCommodityGroupWidget, TextilesCommodityWidget


def _get_shipping_year_selection():
    """Get year selection for Textiles (Quota) applications."""
    current_year = datetime.date.today().year

    return range(current_year, current_year + 10)


class EditTextilesForm(forms.ModelForm):
    class Meta:
        model = models.TextilesApplication
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
            "category_commodity_group": TextilesCategoryCommodityGroupWidget(
                attrs={
                    "data-minimum-input-length": 0,
                    "data-placeholder": "Please choose a category",
                },
            ),
            "commodity": TextilesCommodityWidget(
                attrs={
                    "data-minimum-input-length": 0,
                    "data-placeholder": "Please choose a commodity",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: ICMSLST-425 filter users here correctly (users with access to the importer)
        self.fields["contact"].queryset = User.objects.all()

        self.fields["goods_cleared"].required = True
        self.fields["goods_cleared"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]

        self.fields["origin_country"].queryset = Country.objects.filter(
            country_groups__name="Textile COOs"
        )

        self.fields["consignment_country"].queryset = Country.objects.filter(
            country_groups__name="Textile COCs"
        )
