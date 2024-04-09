from django import forms

from web.domains.file.utils import ImageFileField

from .models import Signature


class SignatureForm(forms.ModelForm):
    class Meta:
        model = Signature
        fields = ("name", "signatory")

    # excluding PNG files as we don't want transparent signature images as they cause issues with the PDF generation,
    # namely, you can see the placeholder signature through the transparent 'real' signature.
    file = ImageFileField(required=True, allowed_extensions=["jpeg", "jpg"])
    is_active = forms.BooleanField(required=False, label="Set Active")
