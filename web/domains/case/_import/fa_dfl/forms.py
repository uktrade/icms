import re
from typing import Any

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.domains.file.utils import ICMSFileField
from web.forms.fields import PastOnlyJqueryDateField
from web.forms.mixins import OptionalFormMixin
from web.models import Country

from . import models


class FirearmDFLFormBase(forms.ModelForm):
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
        self.fields["contact"].queryset = application_contacts(self.instance)

        countries = Country.util.get_all_countries()

        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries


class EditFaDFLForm(OptionalFormMixin, FirearmDFLFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitFaDFLForm(FirearmDFLFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """


class AddDFLGoodsCertificateForm(forms.ModelForm):
    document = ICMSFileField(required=True)

    class Meta:
        model = models.DFLGoodsCertificate
        fields = (
            "goods_description",
            "deactivated_certificate_reference",
            "issuing_country",
        )

        help_texts = {
            "goods_description": (
                "The firearm entered here must correspond with the firearm listed on the deactivation certificate."
                " You must list only one deactivated firearm per goods line."
            )
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        countries = Country.app.get_fa_dfl_issuing_countries()
        self.fields["issuing_country"].queryset = countries

    def clean_goods_description(self):
        description = self.cleaned_data["goods_description"]
        return re.sub(r"\s+", " ", description)


class EditDFLGoodsCertificateForm(forms.ModelForm):
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

        countries = Country.app.get_fa_dfl_issuing_countries()
        self.fields["issuing_country"].queryset = countries

    def clean_goods_description(self):
        description = self.cleaned_data["goods_description"]
        return re.sub(r"\s+", " ", description)


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

    def clean_goods_description(self):
        description = self.cleaned_data["goods_description"]
        return re.sub(r"\s+", " ", description)


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

    def __init__(self, *args: Any, application: models.DFLApplication, **kwargs: Any) -> None:
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
    date_received = PastOnlyJqueryDateField(
        required=True, label="Date Received", year_select_range=6
    )

    class Meta:
        model = models.DFLSupplementaryReport
        fields = ("transport", "date_received", "bought_from")

    def __init__(self, *args: Any, application: models.DFLApplication, **kwargs: Any) -> None:
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
