from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django_filters import CharFilter, ChoiceFilter, FilterSet
from guardian.forms import UserObjectPermissionsForm

from web.errors import APIError
from web.forms.utils import clean_postcode
from web.permissions import ExporterObjectPermissions, Perms
from web.utils.companieshouse import api_get_company

from .models import Exporter


class ExporterFilter(FilterSet):
    status = ChoiceFilter(
        field_name="is_active",
        choices=((True, "Current"), (False, "Archived")),
        lookup_expr="exact",
        label="Status",
        empty_label="Any",
    )
    exporter_name = CharFilter(field_name="name", lookup_expr="icontains", label="Exporter Name")
    agent_name = CharFilter(field_name="agents__name", lookup_expr="icontains", label="Agent Name")

    class Meta:
        model = Exporter
        fields: list[Any] = []

    # Filter base queryset to only get exporters that are not agents.
    @property
    def qs(self):
        return super().qs.filter(main_exporter__isnull=True)


class ExporterForm(forms.ModelForm):
    class Meta:
        model = Exporter
        fields = ["name", "registered_number", "comments"]
        widgets = {"name": forms.Textarea(attrs={"rows": 1})}

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
            address_line_2 = office_address.get("address_line_2")
            locality = office_address.get("locality")
            postcode = office_address.get("postal_code")

            if postcode:
                postcode = clean_postcode(postcode)

            if address_line_1 and postcode:
                instance.offices.get_or_create(
                    address_1=address_line_1,
                    postcode=postcode,
                    defaults={
                        "address_2": address_line_2,
                        "address_4": locality,
                    },
                )

        return instance


class AgentForm(forms.ModelForm):
    main_exporter = forms.ModelChoiceField(
        queryset=Exporter.objects.none(), label="Exporter", disabled=True
    )

    class Meta:
        model = Exporter
        fields = ["main_exporter", "name", "registered_number", "comments"]
        widgets = {"name": forms.Textarea(attrs={"rows": 1})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        exporter = Exporter.objects.filter(pk=self.initial["main_exporter"])
        self.fields["main_exporter"].queryset = exporter

        self.fields["main_exporter"].required = True
        self.fields["name"].required = True
        self.fields["registered_number"].required = True


# Needed for now because we don't want to show all permissions (everything but the agent)
def get_exporter_object_permissions(
    exporter: Exporter,
) -> list[tuple[ExporterObjectPermissions, str]]:
    """Return object permissions for the Exporter model with a label for each."""

    object_permissions = [
        (Perms.obj.exporter.view, "View Applications / Certificates"),
        (Perms.obj.exporter.edit, "Edit Applications / Vary Certificates"),
    ]

    # The agent should never have the manage_contacts_and_agents permission.
    if not exporter.is_agent():
        object_permissions.append(
            (Perms.obj.exporter.manage_contacts_and_agents, "Approve / Reject Agents and Exporters")
        )

    return object_permissions


class ExporterUserObjectPermissionsForm(UserObjectPermissionsForm):
    obj: Exporter

    def get_obj_perms_field_widget(self):
        return forms.CheckboxSelectMultiple(attrs={"class": "radio-relative"})

    def get_obj_perms_field_choices(self):
        # Only iterate over permissions we show in the main edit exporter view
        return [(p.codename, label) for (p, label) in get_exporter_object_permissions(self.obj)]
