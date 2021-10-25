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


class DFLSupplementaryInfoForm(forms.ModelForm):
    class Meta:
        model = models.DFLSupplementaryInfo
        fields = ("no_report_reason",)
        widgets = {"no_report_reason": forms.Textarea({"rows": 3})}

    def __init__(self, *args, application: models.DFLApplication, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.application = application

        if not self.instance.reports.exists():
            self.fields["no_report_reason"].required = True

    def clean(self) -> dict[str, Any]:
        if self.application.importcontact_set.exists() and not self.instance.reports.exists():
            msg = (
                "You must provide the details of who you bought the items from and one or more"
                " firearms reports before you can complete reporting. Each report must include the"
                " means of transport, the date the firearms were received and the details of who"
                " you bought the items from."
            )

            self.add_error(None, msg)

        return super().clean()


class DFLSupplementaryReportForm(forms.ModelForm):
    class Meta:
        model = models.DFLSupplementaryReport
        fields = ("transport", "date_received", "bought_from")
        widgets = {"date_received": DateInput}

    def __init__(self, *args, application: models.DFLApplication, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.application = application
        self.fields["bought_from"].queryset = self.application.importcontact_set.all()

    def clean(self) -> dict[str, Any]:
        """Check all goods in the application have been included in the report"""

        cleaned_data = super().clean()

        # Return cleaned data if creating a new model instance
        if not self.instance.pk:
            return cleaned_data

        if self.application.goods_certificates.filter(is_active=True).exclude(
            supplementary_report_firearms__report=self.instance
        ):
            self.add_error(None, "You must enter this item.")

        return cleaned_data


class DFLSupplementaryReportFirearmForm(forms.ModelForm):
    class Meta:
        model = models.DFLSupplementaryReportFirearm
        fields = ("serial_number", "calibre", "model", "proofing")


class DFLSupplementaryReportUploadFirearmForm(forms.ModelForm):
    file = ICMSFileField(required=True)

    class Meta:
        model = models.DFLSupplementaryReportFirearm
        fields = ("file",)
