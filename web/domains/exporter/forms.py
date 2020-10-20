from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django_filters import CharFilter, FilterSet

from web.company.companieshouse import api_get_company

from .models import Exporter


class ExporterFilter(FilterSet):
    exporter_name = CharFilter(field_name="name", lookup_expr="icontains", label="Exporter Name")

    agent_name = CharFilter(field_name="agents__name", lookup_expr="icontains", label="Agent Name")

    class Meta:
        model = Exporter
        fields = []


class ExporterForm(ModelForm):
    class Meta:
        model = Exporter
        fields = ["name", "registered_number", "comments"]
        labels = {"name": "Organisation Name"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["registered_number"].required = True

    def clean_registered_number(self):
        registered_number = self.cleaned_data["registered_number"]
        self.company = api_get_company(registered_number)
        if not self.company:
            raise ValidationError("Company is not present in Companies House records")
        return registered_number

    def save(self, commit=True):
        instance = super().save(commit)
        if commit:
            office_address = self.company.get("registered_office_address", {})
            address_line_1 = office_address.get("address_line_1")
            locality = office_address.get("locality")
            postcode = office_address.get("postal_code")
            if address_line_1 and postcode:
                instance.offices.create(address=f"{address_line_1}\n{locality}", postcode=postcode)
        return instance
