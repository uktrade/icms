from typing import Any

from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.domains.country.models import Country
from web.domains.file.utils import ICMSFileField
from web.forms.widgets import DateInput

from . import models


class PrepareOILForm(forms.ModelForm):
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
            "know_bought_from",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["know_bought_from"].required = True

        self.fields["contact"].queryset = application_contacts(self.instance)

        # The default label for unknown is "Unknown"
        self.fields["know_bought_from"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]

        self.fields["origin_country"].empty_label = None
        self.fields["consignment_country"].empty_label = None

        countries = Country.objects.filter(name="Any Country", is_active=True)
        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries


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


class OILSupplementaryReportForm(forms.ModelForm):
    class Meta:
        model = models.OILSupplementaryReport
        fields = ("transport", "date_received", "bought_from")
        widgets = {"date_received": DateInput}

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
