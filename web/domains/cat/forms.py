from django import forms

from web.domains.case.export.models import ExportApplicationType


class SearchCATForm(forms.Form):
    template_name = forms.CharField()
    application_type = forms.ChoiceField(
        choices=[("any", "Any")] + ExportApplicationType.Types.choices
    )
    status = forms.ChoiceField(
        choices=(("any", "Any"), ("current", "Current"), ("archived", "Archived"))
    )
