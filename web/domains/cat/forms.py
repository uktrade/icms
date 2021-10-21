from django import forms

from web.domains.case.export.models import ExportApplicationType
from web.domains.cat.models import CertificateApplicationTemplate


class SearchCATForm(forms.Form):
    template_name = forms.CharField()
    application_type = forms.ChoiceField(
        choices=[("any", "Any")] + ExportApplicationType.Types.choices
    )
    status = forms.ChoiceField(
        choices=(("any", "Any"), ("current", "Current"), ("archived", "Archived"))
    )


class CreateCATForm(forms.ModelForm):
    class Meta:
        model = CertificateApplicationTemplate
        fields = ("application_type", "name", "description", "sharing")
        widgets = {"description": forms.Textarea({"rows": 4})}


class EditCATForm(forms.ModelForm):
    class Meta:
        model = CertificateApplicationTemplate
        fields = ("name", "description", "sharing")
        widgets = {"description": forms.Textarea({"rows": 4})}
