from django import forms
from guardian.shortcuts import get_users_with_perms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.country.models import Country
from web.domains.file.utils import ICMSFileField
from web.forms.widgets import DateInput

from .models import DerogationsApplication, DerogationsChecklist


class DerogationsForm(forms.ModelForm):
    commodity_code = forms.ChoiceField(
        label="Commodity Code",
        help_text="""
            It is the responsibility of the applicant to ensure that the commodity code in
            this box is correct. If you are unsure of the correct commodity code,
            consult the HM Revenue and Customs Integrated Tariff Book, Volume 2,
            which is available from the Stationery Office. If you are still in doubt,
            contact the Classification Advisory Service on (01702) 366077.
        """,
        choices=[(x, x) for x in [None, "4403201110", "4403201910", "4403203110", "4403203910"]],
        required=True,
    )

    class Meta:
        model = DerogationsApplication
        fields = (
            "contact",
            "applicant_reference",
            "origin_country",
            "consignment_country",
            "contract_sign_date",
            "contract_completion_date",
            "explanation",
            "commodity_code",
            "goods_description",
            "quantity",
            "unit",
            "value",
        )
        widgets = {
            "contract_sign_date": DateInput,
            "contract_completion_date": DateInput,
            "explanation": forms.Textarea(attrs={"cols": 50, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: ICMSLST-425 filter users here correctly (users with access to the importer)
        users = get_users_with_perms(
            self.instance.importer, only_with_perms_in=["is_contact_of_importer"]
        )
        self.fields["contact"].queryset = users.filter(is_active=True)

        countries = Country.objects.filter(country_groups__name="Derogation from Sanctions COOs")
        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries


class SupportingDocumentForm(forms.Form):
    document = ICMSFileField(required=True)


class SubmitDerogationsForm(forms.Form):
    confirmation = forms.CharField(
        label='Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]

        if confirmation != "I AGREE":
            raise forms.ValidationError("Please agree to the declaration of truth.")

        return confirmation


class DerogationsChecklistForm(ChecklistBaseForm):
    class Meta:
        model = DerogationsChecklist

        fields = ("supporting_document_received",) + ChecklistBaseForm.Meta.fields


class DerogationsChecklistOptionalForm(DerogationsChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class GoodsDerogationsLicenceForm(forms.ModelForm):
    quantity = forms.DecimalField()
    unit = forms.ChoiceField(
        label="Unit",
        choices=[(x, x) for x in ["kilos"]],
    )

    value = forms.CharField(
        label="Value (euro CIF)",
        required=True,
    )

    class Meta:
        model = DerogationsApplication
        fields = ("commodity_code", "goods_description", "quantity", "unit", "value")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commodity_code"].widget.attrs["readonly"] = True
