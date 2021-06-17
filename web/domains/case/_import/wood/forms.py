import datetime

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.file.utils import ICMSFileField
from web.domains.user.models import User
from web.forms.widgets import DateInput

from . import models


def _get_year_selection():
    """Get year selection for wood quota applications. These show last year and
    11 future years."""

    last_year = datetime.date.today().year - 1

    return range(last_year, last_year + 12)


class PrepareWoodQuotaForm(forms.ModelForm):
    shipping_year = forms.IntegerField(
        help_text="""Year of shipment should normally be that shown on any
        export licence or other export authorisation from the exporting country
        covered by this application. Shipment is considered to have taken place
        when the goods are loaded onto the exporting aircraft, vehicle or
        vessel.""",
        widget=forms.Select(choices=[(x, x) for x in _get_year_selection()]),
    )

    exporter_address = forms.CharField(
        label="Exporter address", widget=forms.Textarea(attrs={"rows": 4})
    )

    exporter_vat_nr = forms.CharField(label="Exporter VAT number")

    commodity_code = forms.ChoiceField(
        help_text=""" It is the responsibility of the applicant to ensure that
        the commodity code in this box is correct. If you are unsure of the
        correct commodity code, consult the HM Revenue and Customs Integrated
        Tariff Book, Volume 2, which is available from the Stationery Office. If
        you are still in doubt, contact the Classification Advisory Service on
        (01702) 366077.""",
        choices=[(x, x) for x in [None, "4403201110", "4403201910", "4403203110", "4403203910"]],
    )

    goods_qty = forms.DecimalField(label="Quantity")

    goods_unit = forms.ChoiceField(
        label="Unit",
        choices=[(x, x) for x in ["cubic metres"]],
    )

    additional_comments = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))

    class Meta:
        model = models.WoodQuotaApplication
        fields = (
            "contact",
            "applicant_reference",
            "shipping_year",
            "exporter_name",
            "exporter_address",
            "exporter_vat_nr",
            "commodity_code",
            "goods_description",
            "goods_qty",
            "goods_unit",
            "additional_comments",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: ICMSLST-425 filter users here correctly (users with access to the importer)
        self.fields["contact"].queryset = User.objects.all()


class SupportingDocumentForm(forms.Form):
    document = ICMSFileField(required=True)


class AddContractDocumentForm(forms.Form):
    document = ICMSFileField(required=True)

    reference = forms.CharField(
        help_text="Enter the reference number of the contract/pre-contract between the importer and exporter.",
        required=True,
    )

    contract_date = forms.DateField(
        help_text="Enter the date of the contract/pre-contract between the importer and exporter.",
        required=True,
        widget=DateInput(),
    )


class EditContractDocumentForm(forms.ModelForm):
    reference = forms.CharField(
        help_text="Enter the reference number of the contract/pre-contract between the importer and exporter.",
        required=True,
    )

    contract_date = forms.DateField(
        help_text="Enter the date of the contract/pre-contract between the importer and exporter.",
        required=True,
        widget=DateInput(),
    )

    class Meta:
        model = models.WoodContractFile
        fields = (
            "reference",
            "contract_date",
        )


class SubmitWoodQuotaForm(forms.Form):
    confirmation = forms.CharField(
        label='Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]

        if confirmation != "I AGREE":
            raise forms.ValidationError("Please agree to the declaration of truth.")

        return confirmation


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
    goods_qty = forms.DecimalField(label="Quantity")

    goods_unit = forms.ChoiceField(
        label="Unit",
        choices=[(x, x) for x in ["cubic metres"]],
    )

    class Meta:
        model = models.WoodQuotaApplication
        fields = ("commodity_code", "goods_description", "goods_qty", "goods_unit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity_code"].widget.attrs["readonly"] = True
