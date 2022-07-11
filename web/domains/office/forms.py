from django import forms

from web.domains.office.models import Office


class OfficeEORIForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = [
            "address_1",
            "address_2",
            "address_3",
            "address_4",
            "address_5",
            "postcode",
            "eori_number",
        ]


class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ["address_1", "address_2", "address_3", "address_4", "address_5", "postcode"]
