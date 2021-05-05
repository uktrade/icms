from django import forms
from guardian.shortcuts import get_users_with_perms

from web.domains.country.models import Country
from web.domains.file.utils import ICMSFileField
from web.domains.user.models import User
from web.forms.widgets import DateInput

from .models import DerogationsApplication, DerogationsChecklist


class DerogationsForm(forms.ModelForm):
    contact = forms.ModelChoiceField(
        queryset=User.objects.none(),
        help_text="Select the main point of contact for the case. This will usually be the person who created the application.",
    )
    applicant_reference = forms.CharField(
        label="Applicant's Reference",
        help_text="Enter your own reference for this application.",
        required=False,
    )
    origin_country = forms.ModelChoiceField(
        label="Country Of Origin",
        queryset=Country.objects.filter(country_groups__name="Derogation from Sanctions COOs"),
        required=True,
    )
    consignment_country = forms.ModelChoiceField(
        label="Country Of Consignment",
        queryset=Country.objects.filter(country_groups__name="Derogation from Sanctions COOs"),
        required=True,
    )
    contract_sign_date = forms.DateField(
        label="Contract Sign Date", required=True, widget=DateInput
    )
    contract_completion_date = forms.DateField(
        label="Contract Completion Date", required=True, widget=DateInput
    )
    explanation = forms.CharField(
        label="Provide details of why this is a pre-existing contract",
        required=True,
        widget=forms.Textarea(attrs={"cols": 50, "rows": 3}),
    )

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

    goods_description = forms.CharField(
        label="Goods Description",
        help_text="Details of the goods that are subject to the contract notification",
        required=True,
    )
    quantity = forms.CharField(
        required=True,
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = get_users_with_perms(
            self.instance.importer, only_with_perms_in=["is_contact_of_importer"]
        )
        self.fields["contact"].queryset = users.filter(is_active=True)


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


class DerogationsChecklistForm(forms.ModelForm):
    class Meta:
        model = DerogationsChecklist

        fields = (
            "supporting_document_received",
            "case_update",
            "fir_required",
            "response_preparation",
            "validity_period_correct",
            "endorsements_listed",
            "authorisation",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].required = True


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
