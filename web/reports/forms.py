import datetime as dt

from django import forms
from django_select2.forms import Select2MultipleWidget

from web.forms.fields import JqueryDateField
from web.models import (
    ExportApplicationType,
    ImportApplicationType,
    ProductLegislation,
    ScheduleReport,
)

from .constants import DateFilterType, UserDateFilterType


class BasicReportForm(forms.ModelForm):
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


class ReportForm(BasicReportForm):
    class Meta:
        model = BasicReportForm.Meta.model
        fields = BasicReportForm.Meta.fields

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_to and date_from:
            if date_to < date_from:
                self.add_error("date_to", "Date cannot be earlier than date from field")
            if (date_to - date_from) > dt.timedelta(weeks=105):
                self.add_error("date_from", "Date range cannot be greater than 2 years")
                self.add_error("date_to", "Date range cannot be greater than 2 years")
        return cleaned_data


class IssuedCertificatesForm(ReportForm):
    application_type = forms.ChoiceField(
        choices=[(None, "All")] + ExportApplicationType.Types.choices,
        required=False,
    )

    legislation = forms.ModelMultipleChoiceField(
        queryset=ProductLegislation.objects.filter(is_active=True),
        widget=Select2MultipleWidget(
            attrs={"data-minimum-input-length": 0, "data-placeholder": "Select Legislation"},
        ),
        required=False,
    )

    def clean_legislation(self) -> list:
        legislation = self.cleaned_data.get("legislation")
        if legislation:
            return list(legislation.values_list("pk", flat=True))
        return []

    class Meta:
        model = ReportForm.Meta.model
        fields = ["application_type", "legislation"] + ReportForm.Meta.fields
        help_texts = {
            "date_from": "Application Submitted date (inclusive of this day ie 1-Jan-24 00:00:01)",
            "date_to": "Application Completed date (inclusive of this day ie 31-Jan-24 23:59:59)",
        }


class ImportLicenceForm(ReportForm):
    application_type = forms.ChoiceField(
        choices=[(None, "All")] + ImportApplicationType.Types.choices, required=False
    )
    date_filter_type = forms.ChoiceField(
        choices=DateFilterType.choices, initial=DateFilterType.SUBMITTED
    )

    class Meta:
        model = ReportForm.Meta.model
        fields = ["application_type", "date_filter_type"] + ReportForm.Meta.fields
        help_texts = {
            "date_from": "Application Submitted/Initially closed date (inclusive of this day ie 1-Jan-24 00:00:01)",
            "date_to": "Application Submitted/Initially closed date (inclusive of this day ie 31-Jan-24 23:59:59)",
        }


class ActiveUserForm(BasicReportForm):
    date_filter_type = forms.ChoiceField(
        choices=UserDateFilterType.choices, initial=UserDateFilterType.DATE_JOINED
    )

    class Meta:
        model = ReportForm.Meta.model
        fields = ["date_filter_type"] + ReportForm.Meta.fields
        help_texts = {
            "date_from": "Date joined/Last login date (inclusive of this day ie 1-Jan-24 00:00:01)",
            "date_to": "Date joined/Last login date (inclusive of this day ie 31-Jan-24 23:59:59)",
        }
