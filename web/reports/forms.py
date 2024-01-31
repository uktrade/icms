from datetime import timedelta

from django import forms

from web.forms.fields import JqueryDateField
from web.models import ExportApplicationType, ScheduleReport


class ReportForm(forms.ModelForm):
    class Meta:
        model = ScheduleReport
        fields = ["title", "notes"]

    date_from = JqueryDateField(
        label="Date from",
        help_text="Date (inclusive of this day ie 1-Jan-24 00:00:01)",
    )
    date_to = JqueryDateField(
        label="Date to",
        help_text="Date (inclusive of this day ie 31-Jan-24 23:59:59)",
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_to and date_from:
            if date_to < date_from:
                self.add_error("date_to", "Date cannot be earlier than date from field")
            if (date_to - date_from) > timedelta(weeks=105):
                self.add_error("date_from", "Date range cannot be greater than 2 years")
                self.add_error("date_to", "Date range cannot be greater than 2 years")
        return cleaned_data


class IssuedCertificatesForm(ReportForm):
    application_type = forms.ChoiceField(
        choices=[(None, "All")] + ExportApplicationType.Types.choices, required=False
    )

    class Meta:
        model = ReportForm.Meta.model
        fields = ["application_type"] + ReportForm.Meta.fields
        help_texts = {
            "date_from": "Application Submitted date (inclusive of this day ie 1-Jan-24 00:00:01)",
            "date_to": "Application Completed date (inclusive of this day ie 31-Jan-24 23:59:59)",
        }
