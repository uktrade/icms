from django import forms

from web.forms.fields import UKPostcodeField
from web.models import Office


class ImporterOfficeEORIForm(forms.ModelForm):
    # Importer postcode sent to CHIEF/CDS must be valid
    postcode = UKPostcodeField(required=True)

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


class ImporterOfficeForm(forms.ModelForm):
    # Importer postcode sent to CHIEF/CDS must be valid
    postcode = UKPostcodeField(required=True)

    class Meta:
        model = Office
        fields = ["address_1", "address_2", "address_3", "address_4", "address_5", "postcode"]


class ExporterOfficeForm(forms.ModelForm):
    """Exporter office address can contain more than 5 address lines"""

    class Meta:
        model = Office
        fields = [
            "address_1",
            "address_2",
            "address_3",
            "address_4",
            "address_5",
            "address_6",
            "address_7",
            "address_8",
            "postcode",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["postcode"].required = False
