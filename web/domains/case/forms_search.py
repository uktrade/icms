import datetime as dt

from django import forms
from django_select2.forms import Select2MultipleWidget

from web.domains.case.models import ApplicationBase
from web.domains.contacts.widgets import ContactWidget
from web.forms.fields import JqueryDateField, WildcardField
from web.models import (
    CommodityGroup,
    Country,
    ExportApplicationType,
    ImportApplication,
    ImportApplicationType,
    Process,
    User,
)
from web.models.shared import YesNoChoices
from web.permissions import get_all_case_officers
from web.utils.search import get_export_status_choices, get_import_status_choices

# We are restricting what the user can enter in the regex search fields rather than having to
# escape everything in the search code later.
# Following characters allowed:
# % (The wildcard character)
# \s Any whitespace
# \w Matches any alphanumeric character; this is equivalent to the class [a-zA-Z0-9_].
# Any of the following symbols: ' " , / & @ - \ ( )
wildcard_field_regex = r"^[\w\s'\",\&@\\/\-\(\)\%]+$"
wildcard_invalid_error = "Enter a valid value, see help text for more information"


class SearchFormBase(forms.Form):
    case_ref = WildcardField(
        label="Case Reference",
        required=False,
        regex=wildcard_field_regex,
        error_messages={"invalid": wildcard_invalid_error},
    )

    licence_ref = WildcardField(
        label="Licence Reference",
        required=False,
        regex=wildcard_field_regex,
        error_messages={"invalid": wildcard_invalid_error},
    )

    decision = forms.ChoiceField(
        label="Response Decision",
        choices=[(None, "Any")] + list(ApplicationBase.DECISIONS),
        required=False,
    )

    submitted_from = JqueryDateField(label="Submitted Date", required=False)
    submitted_to = JqueryDateField(label="To", required=False)

    reassignment = forms.BooleanField(label="Reassignment", required=False)

    reassignment_user = forms.ModelChoiceField(
        label="Case Officer",
        help_text=(
            "Search a contact. Contacts returned are matched against first/last name,"  # /PS-IGNORE
            " email, job title, organisation and department."
        ),
        queryset=User.objects.none(),
        widget=ContactWidget(
            attrs={"data-minimum-input-length": 1, "data-placeholder": "Search Users"}
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["reassignment_user"].queryset = get_all_case_officers()

    @staticmethod
    def dates_are_reversed(date_from: dt.date | None, date_to: dt.date | None) -> bool:
        """Check if two dates are in reversed (wrong) order."""
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

    importer_or_agent = WildcardField(
        label="Importer/Agent",
        required=False,
        regex=wildcard_field_regex,
        error_messages={"invalid": wildcard_invalid_error},
    )

    licence_from = JqueryDateField(label="Licence Date", required=False)
    licence_to = JqueryDateField(label="To", required=False)

    issue_from = JqueryDateField(label="Issue Date", required=False)
    issue_to = JqueryDateField(label="To", required=False)

    def clean(self):
        cd = super().clean()

        if self.dates_are_reversed(cd.get("licence_from"), cd.get("licence_to")):
            self.add_error("licence_to", "'From' must be before 'To'")

        if self.dates_are_reversed(cd.get("issue_from"), cd.get("issue_to")):
            self.add_error("issue_to", "'From' must be before 'To'")

        if not cd["reassignment"] and cd["reassignment_user"]:
            self.add_error(
                "reassignment", "Can't search using 'Reassignment To' without Reassignment enabled"
            )

        return cd


class ImportSearchAdvancedForm(ImportSearchForm):
    applicant_ref = WildcardField(
        label="Applicant's Reference",
        required=False,
        regex=wildcard_field_regex,
        error_messages={"invalid": wildcard_invalid_error},
    )

    licence_type = forms.ChoiceField(
        label="Licence Type",
        choices=[(None, "Any"), ("paper", "Paper"), ("electronic", "Electronic")],
        required=False,
    )

    chief_usage_status = forms.ChoiceField(
        label="CHIEF Usage Status",
        required=False,
        choices=[(None, "Any")] + ImportApplication.ChiefUsageStatus.choices,
    )

    application_contact = WildcardField(
        label="Application Contact",
        required=False,
        regex=wildcard_field_regex,
        error_messages={"invalid": wildcard_invalid_error},
    )

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
        choices=[(None, "Any")] + list((x, x) for x in range(2007, dt.date.today().year + 10)),
    )

    goods_category = forms.ModelChoiceField(
        label="Goods Category",
        required=False,
        queryset=CommodityGroup.objects.all(),
    )

    commodity_code = WildcardField(
        label="Commodity Code",
        required=False,
        regex="^[0-9%]+$",
        error_messages={"invalid": wildcard_invalid_error},
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        countries = Country.util.get_all_countries()

        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries

    def clean_commodity_code(self):
        cc = self.cleaned_data["commodity_code"]

        if cc and len(cc.strip("%")) < 3:
            self.add_error("commodity_code", "Please enter at least 3 non wildcard characters.")

        return cc


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

    exporter_or_agent = WildcardField(
        label="Exporter/Agent Name",
        required=False,
        regex=wildcard_field_regex,
        error_messages={"invalid": wildcard_invalid_error},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["licence_ref"].label = "Certificate Reference"
        self.fields["decision"].label = "Case Decision"


class ExportSearchAdvancedForm(ExportSearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        countries = Country.util.get_all_countries()

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


class ReassignmentUserForm(forms.Form):
    assign_to = forms.ModelChoiceField(
        label="Reassign To",
        help_text=(
            "Search a contact. Contacts returned are matched against first/last name,"  # /PS-IGNORE
            " email, job title, organisation and department."
        ),
        queryset=User.objects.none(),
        widget=ContactWidget(
            attrs={"data-minimum-input-length": 1, "data-placeholder": "Search Users"}
        ),
        required=True,
    )

    applications = forms.ModelMultipleChoiceField(
        queryset=Process.objects.none(), widget=forms.CheckboxSelectMultiple, required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["assign_to"].queryset = get_all_case_officers()
        self.fields["applications"].queryset = Process.objects.all()
