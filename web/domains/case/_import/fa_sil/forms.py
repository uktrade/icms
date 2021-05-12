from django import forms
from guardian.shortcuts import get_users_with_perms

from web.domains.country.models import Country
from web.domains.user.models import User

from . import models


class PrepareSILForm(forms.ModelForm):
    applicant_reference = forms.CharField(
        label="Applicant's Reference",
        help_text="Enter your own reference for this application.",
        required=False,
    )

    contact = forms.ModelChoiceField(
        queryset=User.objects.none(),
        help_text="Select the main point of contact for the case. This will usually be the person who created the application.",
    )

    section1 = forms.BooleanField(required=False, label="Firearms Licence for")
    section2 = forms.BooleanField(required=False, label="")
    section5 = forms.BooleanField(required=False, label="")
    section58_obsolete = forms.BooleanField(required=False, label="")
    section58_other = forms.BooleanField(required=False, label="")
    other_description = forms.CharField(
        required=False,
        label="Other Section Description",
        help_text=(
            "If you have selected Other in Firearms Act Sections. Please explain why you are making"
            " this request under this 'Other' section."
        ),
    )

    commodity_code = forms.ChoiceField(
        label="Commodity Code",
        help_text=(
            "You must pick the commodity code group that applies to the items that you wish to"
            ' import. Please note that "ex Chapter 97" is only relevant to collectors pieces and'
            " items over 100 years old. Please contact HMRC classification advisory service,"
            " 01702 366077, if you are unsure of the correct code."
        ),
        choices=[(x, x) for x in [None, "ex Chapter 93", "ex Chapter 97"]],
    )

    origin_country = forms.ModelChoiceField(
        label="Country Of Origin",
        queryset=Country.objects.filter(country_groups__name="Firearms and Ammunition (SIL) COOs"),
    )

    consignment_country = forms.ModelChoiceField(
        label="Country Of Consignment",
        queryset=Country.objects.filter(country_groups__name="Firearms and Ammunition (SIL) COCs"),
    )

    additional_comments = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))

    class Meta:
        model = models.SILApplication
        fields = (
            "contact",
            "applicant_reference",
            "section1",
            "section2",
            "section5",
            "section58_obsolete",
            "section58_other",
            "other_description",
            "origin_country",
            "consignment_country",
            "military_police",
            "eu_single_market",
            "manufactured",
            "know_bought_from",
            "additional_comments",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = get_users_with_perms(
            self.instance.importer, only_with_perms_in=["is_contact_of_importer"]
        )
        self.fields["contact"].queryset = users.filter(is_active=True)

        self.fields["know_bought_from"].required = True
        self.fields["military_police"].required = True
        self.fields["eu_single_market"].required = True
        self.fields["manufactured"].required = True

        yes_no_fields = ["know_bought_from", "military_police", "eu_single_market", "manufactured"]
        for field in yes_no_fields:
            # The default label for unknown is "Unknown"
            self.fields[field].widget.choices = [
                ("unknown", "---------"),
                ("true", "Yes"),
                ("false", "No"),
            ]

    def clean(self):
        cleaned_data = super().clean()

        # At least one section should be selected
        licence_for = ["section1", "section2", "section5", "section58_obsolete", "section58_other"]
        sections = (cleaned_data.get(section) for section in licence_for)
        if not any(sections):
            # The sections are grouped together, error message is added to the last element of the group.
            # Having empty strings will highlight the fields in red.
            self.add_error("section1", "")
            self.add_error("section2", "")
            self.add_error("section5", "")
            self.add_error("section58_obsolete", "")
            self.add_error("section58_other", "You must select at least one item")

        if cleaned_data.get("section58_other") and not cleaned_data.get("other_description"):
            self.add_error("other_description", "You must enter this item")


class SILGoodsSection1Form(forms.ModelForm):
    class Meta:
        models = models.SILGoodsSection1
        fields = ("manufacture", "description", "quantity")


class SILGoodsSection2Form(forms.ModelForm):
    class Meta:
        models = models.SILGoodsSection2
        fields = ("manufacture", "description", "quantity")


class SILGoodsSection5Form(forms.ModelForm):
    class Meta:
        models = models.SILGoodsSection5
        fields = ("subsection", "manufacture", "description", "quantity", "unlimited_quantity")


class SILGoodsSection582ObsoleteForm(forms.ModelForm):
    class Meta:
        models = models.SILGoodsSection582Obsolete
        fields = (
            "curiosity_ornament",
            "acknowledgment",
            "centrefire",
            "manufacture",
            "original_chambering",
            "obsolete_calibre",
            "description",
            "quantity",
        )


class SILGoodsSection582Other(forms.ModelForm):
    class Meta:
        models = models.SILGoodsSection582Other
        fields = (
            "curiosity_ornament",
            "acknowledgment",
            "muzzle_loading",
            "rimfire",
            "rimfire_details",
            "ignition",
            "ignition_details",
            "chamber",
            "bore",
            "bore_details",
            "description",
            "quantity",
        )
