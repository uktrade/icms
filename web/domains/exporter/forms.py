from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField, ModelForm, Textarea
from django_filters import CharFilter, FilterSet

from web.errors import APIError
from web.utils.companieshouse import api_get_company

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
        widgets = {"name": Textarea(attrs={"rows": 1})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["registered_number"].required = True

    def clean_registered_number(self):
        registered_number = self.cleaned_data["registered_number"]

        # this is parsed in save()
        try:
            self.company = api_get_company(registered_number)
        except APIError as e:
            raise ValidationError(e.error_msg)

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


class AgentForm(ModelForm):
    main_exporter = ModelChoiceField(
        queryset=Exporter.objects.none(), label="Exporter", disabled=True
    )

    class Meta:
        model = Exporter
        fields = ["main_exporter", "name", "registered_number", "comments"]
        widgets = {"name": Textarea(attrs={"rows": 1})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        exporter = Exporter.objects.filter(pk=self.initial["main_exporter"])
        self.fields["main_exporter"].queryset = exporter

        self.fields["main_exporter"].required = True
        self.fields["name"].required = True
        self.fields["registered_number"].required = True
