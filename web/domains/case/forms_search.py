import datetime
from typing import Optional

from django import forms

from web.domains.case._import.models import ImportApplicationType
from web.domains.case.export.models import ExportApplicationType
from web.domains.case.models import ApplicationBase
from web.forms.widgets import DateInput
from web.models.shared import YesNoChoices


class SearchFormBase(forms.Form):
    case_ref = forms.CharField(label="Case reference", required=False)

    licence_ref = forms.CharField(label="Licence reference", required=False)

    decision = forms.ChoiceField(
        label="Decision",
        choices=[(None, "Any")] + list(ApplicationBase.DECISIONS),  # type:ignore[arg-type]
        required=False,
    )

    submitted_from = forms.DateField(label="Submitted date", required=False, widget=DateInput)
    submitted_to = forms.DateField(label="To", required=False, widget=DateInput)

    reassignment = forms.BooleanField(label="Reassignment", required=False)

    @staticmethod
    def dates_are_reversed(
        date_from: Optional[datetime.date], date_to: Optional[datetime.date]
    ) -> bool:
        """Check if two dates are in reversed (wrong) order. """
        if (date_from and date_to) and (date_from > date_to):
            return True

        return False

    def clean(self):
        cd = super().clean()

        if self.dates_are_reversed(cd.get("submitted_from"), cd.get("submitted_to")):
            self.add_error("submitted_to", "'From' must be before 'To'")

        return cd


class ImportSearchForm(SearchFormBase):
    application_type = forms.ChoiceField(
        label="Application type",
        choices=[(None, "Any")] + ImportApplicationType.Types.choices,
        required=False,
    )

    # TODO: add application_subtype only shown when application_type==firearms
    application_sub_type = forms.ChoiceField(
        label="Sub-type",
        choices=[(None, "Any")] + ImportApplicationType.SubTypes.choices,
        required=False,
    )

    status = forms.ChoiceField(
        label="Status",
        choices=[(None, "Any")] + ApplicationBase.Statuses.choices,
        required=False,
    )

    importer_or_agent = forms.CharField(label="Importer/Agent", required=False)

    licence_from = forms.DateField(label="Licence date", required=False, widget=DateInput)
    licence_to = forms.DateField(label="To", required=False, widget=DateInput)

    issue_from = forms.DateField(label="Issue date", required=False, widget=DateInput)
    issue_to = forms.DateField(label="To", required=False, widget=DateInput)

    def clean(self):
        cd = super().clean()

        if self.dates_are_reversed(cd.get("licence_from"), cd.get("licence_to")):
            self.add_error("licence_to", "'From' must be before 'To'")

        if self.dates_are_reversed(cd.get("issue_from"), cd.get("issue_to")):
            self.add_error("issue_to", "'From' must be before 'To'")

        return cd


class ExportSearchForm(SearchFormBase):
    application_type = forms.ChoiceField(
        label="Application type",
        choices=[(None, "Any")] + ExportApplicationType.Types.choices,
        required=False,
    )

    status = forms.ChoiceField(
        label="Status",
        choices=[(None, "Any")] + ApplicationBase.Statuses.choices,
        required=False,
    )

    exporter_or_agent = forms.CharField(label="Exporter/Agent", required=False)

    closed_from = forms.DateField(label="Closed date", required=False, widget=DateInput)
    closed_to = forms.DateField(label="To", required=False, widget=DateInput)

    cert_country = forms.CharField(label="Certificate country", required=False)
    manufacture_country = forms.CharField(label="Country of manufacture", required=False)

    pending_firs = forms.ChoiceField(
        label="Pending Further Information Requests",
        choices=[(None, "Any")] + YesNoChoices.choices,
        required=False,
    )

    pending_update_reqs = forms.ChoiceField(
        label="Pending Update Requests",
        choices=[(None, "Any")] + YesNoChoices.choices,
        required=False,
    )

    def clean(self):
        cd = super().clean()

        if self.dates_are_reversed(cd.get("closed_from"), cd.get("closed_to")):
            self.add_error("closed_to", "'From' must be before 'To'")

        return cd
