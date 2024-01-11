from typing import Any

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.domains.file.utils import ICMSFileField
from web.forms.fields import JqueryDateField
from web.forms.mixins import OptionalFormMixin
from web.models import Country

from . import models


class FirearmOILFormBase(forms.ModelForm):
    section1 = forms.BooleanField(disabled=True, label="Firearms Licence for")
    section2 = forms.BooleanField(disabled=True, label="")

    class Meta:
        model = models.OpenIndividualLicenceApplication
        fields = (
            "contact",
            "applicant_reference",
            "section1",
            "section2",
            "origin_country",
            "consignment_country",
            "commodity_code",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_countries_queryset = Country.objects.filter(name="Any Country", is_active=True)
        self.all_countries_object = self.all_countries_queryset.get()

        locked_location_field_kwargs = {
            "queryset": self.all_countries_queryset,
            "help_text": None,
            "empty_label": None,
            "disabled": True,
        }
        self.fields["origin_country"] = forms.ModelChoiceField(**locked_location_field_kwargs)
        self.fields["consignment_country"] = forms.ModelChoiceField(**locked_location_field_kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

    def clean(self):
        cleaned_data = super().clean()

        # because these fields are disabled, they are included correctly in the cleaned_data
        cleaned_data["origin_country"] = self.all_countries_object
        cleaned_data["consignment_country"] = self.all_countries_object
        return cleaned_data


class EditFaOILForm(OptionalFormMixin, FirearmOILFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitFaOILForm(FirearmOILFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """


class ChecklistFirearmsOILApplicationForm(ChecklistBaseForm):
    class Meta:
        model = models.ChecklistFirearmsOILApplication

        fields = (
            "authority_required",
            "authority_received",
            "authority_police",
        ) + ChecklistBaseForm.Meta.fields

        labels = {
            "validity_period_correct": "Validity period of licence matches that of the RFD certificate?",
        }


class ChecklistFirearmsOILApplicationOptionalForm(ChecklistFirearmsOILApplicationForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class OILSupplementaryInfoForm(forms.ModelForm):
    class Meta:
        model = models.OILSupplementaryInfo
        fields = ("no_report_reason",)
        widgets = {"no_report_reason": forms.Textarea({"rows": 3})}

    def __init__(
        self, *args, application: models.OpenIndividualLicenceApplication, **kwargs
    ) -> None:
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


class OILSupplementaryReportForm(forms.ModelForm):
    date_received = JqueryDateField(required=True, label="Date Received")

    class Meta:
        model = models.OILSupplementaryReport
        fields = ("transport", "date_received", "bought_from")

    def __init__(
        self, *args, application: models.OpenIndividualLicenceApplication, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self.fields["bought_from"].queryset = application.importcontact_set.all()

    def clean(self) -> dict[str, Any]:
        """Check all goods in the application have been included in the report"""

        cleaned_data = super().clean()

        # Return cleaned data if creating a new model instance
        if not self.instance.pk:
            return cleaned_data

        if not self.instance.firearms.exists():
            self.add_error(None, "You must enter this item.")

        return cleaned_data


class OILSupplementaryReportFirearmForm(forms.ModelForm):
    class Meta:
        model = models.OILSupplementaryReportFirearm
        fields = ("serial_number", "calibre", "model", "proofing")


class OILSupplementaryReportUploadFirearmForm(forms.ModelForm):
    file = ICMSFileField(required=True)

    class Meta:
        model = models.OILSupplementaryReportFirearm
        fields = ("file",)
