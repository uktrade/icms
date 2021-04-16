from django import forms

from . import models


class SanctionEmailForm(forms.ModelForm):
    class Meta:
        model = models.SanctionEmail
        fields = ["name", "email"]
