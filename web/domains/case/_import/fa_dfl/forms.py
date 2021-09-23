from typing import Any

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.domains.file.utils import ICMSFileField
from web.forms.widgets import DateInput
from web.models import Country

from . import models


class PrepareDFLForm(forms.ModelForm):
    deactivated_firearm = forms.BooleanField(disabled=True, label="Firearms Licence for")

    class Meta:
        model = models.DFLApplication
        fields = (
            "applicant_reference",
            "deactivated_firearm",
            "proof_checked",
            "origin_country",
            "consignment_country",
            "contact",
            "commodity_code",
            "constabulary",
            "know_bought_from",
        )

        help_texts = {
            "proof_checked": (
                "The firearm must have been proof marked as deactivated in line with current UK requirements"
            ),
            "origin_country": (
                "If the goods originate from more than one country,"
                " select the group (e.g. Any EU Country) that best describes this."
            ),
            "consignment_country": (
                "If the goods are consigned/dispatched from more than one country,"
                " select the group (e.g. Any EU Country) that best describes this."
            ),
            "constabulary": "Select the constabulary in which you reside.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["proof_checked"].required = True
        self.fields["know_bought_from"].required = True

        # The default label for unknown is "Unknown"
        self.fields["know_bought_from"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]

        self.fields["contact"].queryset = application_contacts(self.instance)

        countries = Country.objects.filter(
            country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries",
            is_active=True,
        )
        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries


class AddDLFGoodsCertificateForm(forms.ModelForm):
    document = ICMSFileField(required=True)

    class Meta:
        model = models.DFLGoodsCertificate
        fields = ("goods_description", "deactivated_certificate_reference", "issuing_country")

        help_texts = {
            "goods_description": (
                "The firearm entered here must correspond with the firearm listed on the deactivation certificate."
                " You must list only one deactivated firearm per goods line."
            )
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["issuing_country"].queryset = Country.objects.filter(
            country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries",
            is_active=True,
        )


class EditDLFGoodsCertificateForm(forms.ModelForm):
    class Meta:
        model = models.DFLGoodsCertificate
        fields = ("goods_description", "deactivated_certificate_reference", "issuing_country")

        help_texts = {
            "goods_description": (
                "The firearm entered here must correspond with the firearm listed on the deactivation certificate."
                " You must list only one deactivated firearm per goods line."
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        countries = Country.objects.filter(
            country_groups__name="Firearms and Ammunition (Deactivated) Issuing Countries",
            is_active=True,
        )

        self.fields["issuing_country"].queryset = countries


class EditDFLGoodsCertificateDescriptionForm(forms.ModelForm):
    class Meta:
        model = models.DFLGoodsCertificate
        fields = ("goods_description",)

        help_texts = {
            "goods_description": (
                "The firearm entered here must correspond with the firearm listed on the deactivation certificate."
                " You must list only one deactivated firearm per goods line."
            )
        }


class DFLChecklistForm(ChecklistBaseForm):
    class Meta:
        model = models.DFLChecklist

        fields = (
            "deactivation_certificate_attached",
            "deactivation_certificate_issued",
        ) + ChecklistBaseForm.Meta.fields


class DFLChecklistOptionalForm(DFLChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class DFLSupplementaryReportForm(forms.ModelForm):
    class Meta:
        model = models.DFLSupplementaryReport
        fields = ("transport", "date_received", "bought_from")
        widgets = {"date_received": DateInput}

    def __init__(self, *args, application: models.DFLApplication, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.fields["bought_from"].queryset = application.importcontact_set.all()


class DFLSupplementaryReportFirearmForm(forms.ModelForm):
    class Meta:
        model = models.DFLSupplementaryReportFirearm
        fields = ("serial_number", "calibre", "model", "proofing")
