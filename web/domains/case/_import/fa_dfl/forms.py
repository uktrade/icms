from django import forms
from guardian.shortcuts import get_users_with_perms

from web.models import Country, User

from . import models


class PrepareDFLForm(forms.ModelForm):

    applicant_reference = forms.CharField(
        label="Applicant's Reference",
        help_text="Enter your own reference for this application.",
        required=False,
    )

    deactivated_firearm = forms.BooleanField(disabled=True, label="Firearms Licence for")

    proof_checked = forms.BooleanField(
        required=True,
        label="Proof Checked",
        help_text="The firearm must have been proof marked as deactivated in line with current UK requirements",
    )

    origin_country = forms.ModelChoiceField(
        label="Country Of Origin",
        empty_label=None,
        queryset=Country.objects.filter(
            country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
        ),
        help_text=(
            "If the goods originate from more than one country,"
            " select the group (e.g. Any EU Country) that best describes this."
        ),
    )

    consignment_country = forms.ModelChoiceField(
        label="Country Of Consignment",
        empty_label=None,
        queryset=Country.objects.filter(
            country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries"
        ),
        help_text=(
            "If the goods are consigned/dispatched from more than one country,"
            " select the group (e.g. Any EU Country) that best describes this."
        ),
    )

    contact = forms.ModelChoiceField(
        queryset=User.objects.none(),
        help_text=(
            "Select the main point of contact for the case."
            " This will usually be the person who created the application."
        ),
    )

    class Meta:
        model = models.DFLApplication
        fields = (
            "applicant_reference",
            "deactivated_firearm",
            "proof_checked",
            "origin_country",
            "consignment_country",
            "contact",
            "know_bought_from",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["know_bought_from"].required = True

        # The default label for unknown is "Unknown"
        self.fields["know_bought_from"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]

        users = get_users_with_perms(
            self.instance.importer, only_with_perms_in=["is_contact_of_importer"]
        )
        self.fields["contact"].queryset = users.filter(is_active=True)
