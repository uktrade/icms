from django import forms
from guardian.shortcuts import get_users_with_perms

from web.domains.country.models import Country
from web.domains.user.models import User

from .models import SanctionsAndAdhocApplication, SanctionsAndAdhocApplicationGoods


class SanctionsAndAdhocLicenseForm(forms.ModelForm):
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
        queryset=Country.objects.filter(country_groups__name="Sanctions and Adhoc License"),
    )

    consignment_country = forms.ModelChoiceField(
        label="Country Of Consignment",
        queryset=Country.objects.filter(country_groups__name="Sanctions and Adhoc License"),
    )
    exporter_name = forms.CharField(
        label="Exporter Name",
        required=False,
    )
    exporter_address = forms.CharField(
        label="Exporter Address",
        required=False,
    )

    class Meta:
        model = SanctionsAndAdhocApplication
        fields = (
            "contact",
            "applicant_reference",
            "origin_country",
            "consignment_country",
            "exporter_name",
            "exporter_address",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = get_users_with_perms(
            self.instance.importer, only_with_perms_in=["is_contact_of_importer"]
        )
        self.fields["contact"].queryset = users.filter(is_active=True)


class GoodsForm(forms.ModelForm):
    class Meta:
        # TODO restrict commodities to group when it becomes known
        model = SanctionsAndAdhocApplicationGoods
        fields = ["commodity_code", "goods_description", "quantity_amount", "value"]
        widgets = {
            "goods_description": forms.Textarea(attrs={"cols": 80, "rows": 20}),
        }
        labels = {"value": "Value (GBP CIF)"}
