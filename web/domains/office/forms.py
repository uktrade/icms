from typing import Any

from django import forms

from web.domains.office.utils import normalize_address
from web.forms.fields import UKPostcodeField
from web.models import Office


class BaseImporterOfficeForm(forms.ModelForm):
    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        for address_line in ["address_1", "address_2", "address_3", "address_4", "address_5"]:
            if value := cleaned_data.get(address_line):
                cleaned_data[address_line] = normalize_address(value)

        return cleaned_data


class ImporterOfficeEORIForm(BaseImporterOfficeForm):
    # TODO: Revisit in ECIL-486 part 2
    # Importer postcode sent to CHIEF/CDS must be valid
    postcode = UKPostcodeField(required=False)

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


class ImporterOfficeForm(BaseImporterOfficeForm):
    # TODO: Revisit in ECIL-486 part 2
    # Importer postcode sent to CHIEF/CDS must be valid
    postcode = UKPostcodeField(required=False)

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
