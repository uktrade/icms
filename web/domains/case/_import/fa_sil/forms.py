from django import forms
from guardian.shortcuts import get_users_with_perms

from web.domains.country.models import Country
from web.domains.user.models import User

from . import models

TRUE_FALSE_CHOICES = (
    ("unknown", "---------"),
    (True, "Yes"),
    (False, "No"),
)


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
        model = models.SILGoodsSection1
        fields = ("manufacture", "description", "quantity")
        help_texts = {
            "description": (
                "You no longer need to type the part of the Firearms Act that applies to the"
                " item listed in this box. You must select it from the 'Licence for' section."
            ),
            "quantity": "Enter a whole number",
        }
        widgets = {
            "manufacture": forms.Select(choices=TRUE_FALSE_CHOICES),
            "description": forms.Textarea({"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manufacture"].required = True


class SILGoodsSection2Form(forms.ModelForm):
    class Meta:
        model = models.SILGoodsSection2
        fields = ("manufacture", "description", "quantity")
        help_texts = {
            "description": (
                "You no longer need to type the part of the Firearms Act that applies to the"
                " item listed in this box. You must select it from the 'Licence for' section."
            ),
            "quantity": "Enter a whole number",
        }
        widgets = {
            "manufacture": forms.Select(choices=TRUE_FALSE_CHOICES),
            "description": forms.Textarea({"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manufacture"].required = True


class SILGoodsSection5Form(forms.ModelForm):
    class Meta:
        model = models.SILGoodsSection5
        fields = ("subsection", "manufacture", "description", "quantity", "unlimited_quantity")
        help_texts = {
            "description": (
                "You no longer need to type the part of the Firearms Act that applies to the"
                " item listed in this box. You must select it from the 'Licence for' section."
            ),
            "quantity": "Enter a whole number",
        }
        widgets = {
            "manufacture": forms.Select(choices=TRUE_FALSE_CHOICES),
            "description": forms.Textarea({"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manufacture"].required = True


class SILGoodsSection582ObsoleteForm(forms.ModelForm):
    class Meta:
        model = models.SILGoodsSection582Obsolete
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
        widgets = {
            "curiosity_ornament": forms.Select(choices=TRUE_FALSE_CHOICES),
            "centrefire": forms.Select(choices=TRUE_FALSE_CHOICES),
            "manufacture": forms.Select(choices=TRUE_FALSE_CHOICES),
            "original_chambering": forms.Select(choices=TRUE_FALSE_CHOICES),
            "description": forms.Textarea({"rows": 3}),
        }
        help_texts = {
            "description": (
                "You no longer need to type the part of the Firearms Act that applies to the"
                " item listed in this box. You must select it from the 'Licence for' section."
            ),
            "quantity": "Enter a whole number",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curiosity_ornament"].required = True
        self.fields["centrefire"].required = True
        self.fields["manufacture"].required = True
        self.fields["original_chambering"].required = True


class SILGoodsSection582OtherForm(forms.ModelForm):
    class Meta:
        model = models.SILGoodsSection582Other
        fields = (
            "curiosity_ornament",
            "acknowledgment",
            "manufacture",
            "description",
            "quantity",
            "muzzle_loading",
            "rimfire",
            "rimfire_details",
            "ignition",
            "ignition_details",
            "ignition_other",
            "chamber",
            "bore",
            "bore_details",
        )
        widgets = {
            "curiosity_ornament": forms.Select(choices=TRUE_FALSE_CHOICES),
            "muzzle_loading": forms.Select(choices=TRUE_FALSE_CHOICES),
            "rimfire": forms.Select(choices=TRUE_FALSE_CHOICES),
            "ignition": forms.Select(choices=TRUE_FALSE_CHOICES),
            "chamber": forms.Select(choices=TRUE_FALSE_CHOICES),
            "bore": forms.Select(choices=TRUE_FALSE_CHOICES),
            "description": forms.Textarea({"rows": 3}),
        }
        help_texts = {
            "description": (
                "You no longer need to type the part of the Firearms Act that applies to the"
                " item listed in this box. You must select it from the 'Licence for' section."
            ),
            "chamber": (
                "32 bore, 24 bore, 14 bore, 10 bore (2 5/8 and 2 7/8 inch only), 8 bore, 4 bore,"
                " 3 bore, 2 bore, 1 1/8 bore, 1 1/2 bore, 1 1/4 bore"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curiosity_ornament"].required = True
        self.fields["manufacture"].required = True
        self.fields["muzzle_loading"].required = True
        self.fields["rimfire"].required = True
        self.fields["ignition"].required = True
        self.fields["chamber"].required = True
        self.fields["bore"].required = True
