import datetime
from typing import Optional

from django import forms
from django_select2.forms import Select2MultipleWidget

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.case.export.models import ExportApplicationType
from web.domains.case.models import ApplicationBase
from web.domains.commodity.models import CommodityGroup
from web.domains.country.models import Country
from web.forms.widgets import DateInput
from web.models.shared import YesNoChoices
from web.utils.search import get_export_status_choices, get_import_status_choices


class SearchFormBase(forms.Form):
    case_ref = forms.CharField(label="Case Reference", required=False)

    licence_ref = forms.CharField(label="Licence Reference", required=False)

    decision = forms.ChoiceField(
        label="Response Decision",
        choices=[(None, "Any")] + list(ApplicationBase.DECISIONS),  # type:ignore[arg-type]
        required=False,
    )

    submitted_from = forms.DateField(label="Submitted Date", required=False, widget=DateInput)
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
        label="Application Type",
        choices=[(None, "Any")] + ImportApplicationType.Types.choices,
        required=False,
    )

    # TODO: add application_subtype only shown when application_type==firearms
    application_sub_type = forms.ChoiceField(
        label="Sub-Type",
        choices=[(None, "Any")] + ImportApplicationType.SubTypes.choices,
        required=False,
    )

    status = forms.ChoiceField(
        label="Case Status",
        choices=[(None, "Any")] + get_import_status_choices(),
        required=False,
    )

    importer_or_agent = forms.CharField(label="Importer/Agent", required=False)

    licence_from = forms.DateField(label="Licence Date", required=False, widget=DateInput)
    licence_to = forms.DateField(label="To", required=False, widget=DateInput)

    issue_from = forms.DateField(label="Issue Date", required=False, widget=DateInput)
    issue_to = forms.DateField(label="To", required=False, widget=DateInput)

    def clean(self):
        cd = super().clean()

        if self.dates_are_reversed(cd.get("licence_from"), cd.get("licence_to")):
            self.add_error("licence_to", "'From' must be before 'To'")

        if self.dates_are_reversed(cd.get("issue_from"), cd.get("issue_to")):
            self.add_error("issue_to", "'From' must be before 'To'")

        return cd


class ImportSearchAdvancedForm(ImportSearchForm):
    applicant_ref = forms.CharField(label="Applicant's Reference", required=False)

    licence_type = forms.ChoiceField(
        label="Licence Type",
        choices=[(None, "Any"), ("paper", "Paper"), ("electronic", "Electronic")],
        required=False,
    )

    chief_usage_status = forms.ChoiceField(
        label="CHIEF Usage Status",
        required=False,
        choices=[(None, "Any")] + ImportApplication.ChiefUsageTypes.choices,
    )

    application_contact = forms.CharField(label="Application Contact", required=False)

    origin_country = forms.ModelMultipleChoiceField(
        label="Country of Origin",
        required=False,
        queryset=Country.objects.none(),
        widget=Select2MultipleWidget,
    )

    consignment_country = forms.ModelMultipleChoiceField(
        label="Country of Consignment",
        required=False,
        queryset=Country.objects.none(),
        widget=Select2MultipleWidget,
    )

    shipping_year = forms.ChoiceField(
        label="Shipping Year",
        required=False,
        choices=[(None, "Any")]
        + list((x, x) for x in range(2007, datetime.date.today().year + 10)),  # type:ignore[misc]
    )

    goods_category = forms.ModelChoiceField(
        label="Goods Category",
        required=False,
        queryset=CommodityGroup.objects.all(),
        widget=Select2MultipleWidget,
    )

    commodity_code = forms.CharField(label="Commodity Code", required=False)

    pending_firs = forms.ChoiceField(
        label="Pending Further Information Requests",
        required=False,
        choices=[(None, "Any")] + YesNoChoices.choices,
    )

    pending_update_reqs = forms.ChoiceField(
        label="Pending Update Requests",
        required=False,
        choices=[(None, "Any")] + YesNoChoices.choices,
    )

    under_appeal = forms.ChoiceField(
        label="Under Appeal",
        required=False,
        choices=[(None, "Any")] + YesNoChoices.choices,
    )

    def __init__(self, *args, **kwargs):
        super(ImportSearchAdvancedForm, self).__init__(*args, **kwargs)

        countries = Country.objects.filter(is_active=True, type=Country.SOVEREIGN_TERRITORY)

        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries


class ExportSearchForm(SearchFormBase):
    application_type = forms.ChoiceField(
        label="Application Type",
        choices=[(None, "Any")] + ExportApplicationType.Types.choices,
        required=False,
    )

    status = forms.ChoiceField(
        label="Status",
        choices=[(None, "Any")] + get_export_status_choices(),
        required=False,
    )

    exporter_or_agent = forms.CharField(label="Exporter/Agent Name", required=False)
    closed_from = forms.DateField(label="Closed Date", required=False, widget=DateInput)
    closed_to = forms.DateField(label="To", required=False, widget=DateInput)

    def clean(self):
        cd = super().clean()

        if self.dates_are_reversed(cd.get("closed_from"), cd.get("closed_to")):
            self.add_error("closed_to", "'From' must be before 'To'")

        return cd

    def __init__(self, *args, **kwargs):
        super(ExportSearchForm, self).__init__(*args, **kwargs)
        self.fields["licence_ref"].label = "Certificate Reference"
        self.fields["decision"].label = "Case Decision"


class ExportSearchAdvancedForm(ExportSearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        countries = Country.objects.filter(is_active=True, type=Country.SOVEREIGN_TERRITORY)

        self.fields["certificate_country"].queryset = countries
        self.fields["manufacture_country"].queryset = countries

    application_contact = forms.CharField(label="Application Contact", required=False)

    certificate_country = forms.ModelMultipleChoiceField(
        label="Certificate Country",
        required=False,
        queryset=Country.objects.none(),
        widget=Select2MultipleWidget,
    )

    manufacture_country = forms.ModelMultipleChoiceField(
        label="Country of Manufacture",
        required=False,
        queryset=Country.objects.none(),
        widget=Select2MultipleWidget,
    )

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
