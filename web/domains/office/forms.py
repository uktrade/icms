from web.forms import ModelEditForm
from django import forms
from web.domains.office.models import Office


class OfficeEditForm(ModelEditForm):
    address = forms.CharField(widget=forms.Textarea({'rows': 3, 'required': 'required'}), required=True)

    class Meta:
        model = Office
        fields = ['address', 'postcode', 'eori_number']
