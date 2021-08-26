from django import forms

from web.domains.case._import.models import ImportApplicationType
from web.domains.case.export.models import ExportApplicationType
from web.domains.case.models import ApplicationBase


class SearchFormBase(forms.Form):
    case_ref = forms.CharField(label="ILB Case Reference", required=False)

    licence_ref = forms.CharField(label="ILB Licence Reference", required=False)

    decision = forms.ChoiceField(
        label="Case Decision",
        choices=[(None, "Any")] + list(ApplicationBase.DECISIONS),  # type:ignore[arg-type]
        required=False,
    )


class ImportSearchForm(SearchFormBase):
    application_type = forms.ChoiceField(
        label="Application type",
        choices=[(None, "Any")] + ImportApplicationType.Types.choices,
        required=False,
    )

    status = forms.ChoiceField(
        label="Status",
        # TODO: get choices for import statuses
        choices=[(None, "Any")] + [],
        required=False,
    )


class ExportSearchForm(SearchFormBase):
    application_type = forms.ChoiceField(
        label="Application type",
        choices=[(None, "Any")] + ExportApplicationType.Types.choices,
        required=False,
    )

    status = forms.ChoiceField(
        label="Status",
        # TODO: get choices for export statuses
        choices=[(None, "Any")] + [],
        required=False,
    )
