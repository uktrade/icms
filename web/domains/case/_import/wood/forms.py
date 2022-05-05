import datetime

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.domains.commodity.models import Commodity
from web.domains.file.utils import ICMSFileField
from web.forms.mixins import OptionalFormMixin
from web.forms.widgets import DateInput
from web.utils.commodity import get_active_commodities

from . import models


def _get_year_selection():
    """Get year selection for Wood (quota) applications."""
    current_year = datetime.date.today().year

    return range(current_year, current_year + 11)


class WoodQuotaFormBase(forms.ModelForm):
    shipping_year = forms.IntegerField(
        help_text="""Year of shipment should normally be that shown on any
        export licence or other export authorisation from the exporting country
        covered by this application. Shipment is considered to have taken place
        when the goods are loaded onto the exporting aircraft, vehicle or
        vessel.""",
        widget=forms.Select(choices=[(x, x) for x in _get_year_selection()]),
    )

    class Meta:
        model = models.WoodQuotaApplication
        fields = (
            "contact",
            "applicant_reference",
            "shipping_year",
            "exporter_name",
            "exporter_address",
            "exporter_vat_nr",
            "commodity",
            "goods_description",
            "goods_qty",
            "goods_unit",
            "additional_comments",
        )

        widgets = {
            "exporter_address": forms.Textarea(attrs={"rows": 4}),
            "additional_comments": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

        # Wood applications are simply filtered by commodity type instead of
        # using the usage records to filter commodities.
        self.fields["commodity"].queryset = get_active_commodities(
            Commodity.objects.filter(commodity_type__type="Wood")
        )


class EditWoodQuotaForm(OptionalFormMixin, WoodQuotaFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitWoodQuotaForm(WoodQuotaFormBase):
    """Form used when submitting a wood application.

    All fields are fully validated to ensure form is correct.
    """


class AddContractDocumentForm(forms.ModelForm):
    document = ICMSFileField(required=True)

    class Meta:
        model = models.WoodContractFile
        fields = ("reference", "contract_date")

        widgets = {"contract_date": DateInput()}


class EditContractDocumentForm(forms.ModelForm):
    class Meta:
        model = models.WoodContractFile

        fields = ("reference", "contract_date")

        widgets = {"contract_date": DateInput()}


class WoodQuotaChecklistForm(ChecklistBaseForm):
    class Meta:
        model = models.WoodQuotaChecklist
        fields = ("sigl_wood_application_logged",) + ChecklistBaseForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sigl_wood_application_logged"].required = True


class WoodQuotaChecklistOptionalForm(WoodQuotaChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class GoodsWoodQuotaLicenceForm(forms.ModelForm):
    class Meta:
        model = models.WoodQuotaApplication
        fields = ("commodity", "goods_description", "goods_qty", "goods_unit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity"].disabled = True
