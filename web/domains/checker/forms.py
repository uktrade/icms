from django import forms


class CertificateCheckForm(forms.Form):
    certificate_reference = forms.CharField(max_length=16)
    certificate_code = forms.CharField(max_length=16)
