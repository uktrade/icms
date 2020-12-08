from django import forms

from web.domains.section5.models import Section5Clause


class Section5ClauseForm(forms.ModelForm):
    class Meta:
        model = Section5Clause
        fields = ("clause", "description")
