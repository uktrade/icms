import datetime as dt

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.forms.mixins import OptionalFormMixin
from web.models import Country

from . import models
from .widgets import TextilesCategoryCommodityGroupWidget, TextilesCommodityWidget


def _get_shipping_year_selection():
    """Get year selection for Textiles (Quota) applications."""
    current_year = dt.date.today().year

    return range(current_year, current_year + 11)


class TextilesFormBase(forms.ModelForm):
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

        self.fields["contact"].queryset = application_contacts(self.instance)

        self.fields["goods_cleared"].required = True
        self.fields["goods_cleared"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]

        self.fields["origin_country"].queryset = Country.app.get_textiles_coo_countries()
        self.fields["consignment_country"].queryset = Country.util.get_all_countries()


class EditTextilesForm(OptionalFormMixin, TextilesFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitTextilesForm(TextilesFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """


class TextilesChecklistForm(ChecklistBaseForm):
    class Meta:
        model = models.TextilesChecklist
        fields = ("within_maximum_amount_limit",) + ChecklistBaseForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["within_maximum_amount_limit"].required = True


class TextilesChecklistOptionalForm(TextilesChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class GoodsTextilesLicenceForm(forms.ModelForm):
    class Meta:
        model = models.TextilesApplication
        fields = (
            "category_licence_description",
            "goods_description",
            "quantity",
        )
