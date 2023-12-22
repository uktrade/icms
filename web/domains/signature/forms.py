from django import forms

from web.domains.file.utils import ImageFileField

from .models import Signature


class SignatureForm(forms.ModelForm):
    class Meta:
        model = Signature
        fields = ("name", "signatory")

    file = ImageFileField(required=True)
    is_active = forms.BooleanField(required=False, label="Set Active")
