from django import forms

from web.forms.fields import JqueryDateField


class ValidateSignatureForm(forms.Form):
    date_issued = JqueryDateField(required=True, label="What date was your document issued")
