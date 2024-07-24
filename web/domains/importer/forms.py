from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django_filters import CharFilter, ChoiceFilter, FilterSet
from guardian.forms import UserObjectPermissionsForm

from web.domains.importer.fields import PersonWidget
from web.errors import APIError, CompanyNotFound
from web.forms.utils import clean_postcode
from web.forms.widgets import CheckboxSelectMultiple
from web.models import Importer, Section5Authority
from web.models.shared import ArchiveReasonChoices
from web.permissions import ImporterObjectPermissions, Perms
from web.utils.companieshouse import api_get_company


class ImporterIndividualForm(forms.ModelForm):
    EORI_INDIVIDUAL = "GBPR"

    class Meta:
        model = Importer
        fields = ["user", "eori_number", "region_origin", "comments"]
        widgets = {"user": PersonWidget}
        help_texts = {"eori_number": "EORI number should include the GBPR prefix"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # EORI number is required if it's already in the DB, or if it's a new importer
        if self.instance.eori_number or not self.instance.pk:
            self.fields["eori_number"].required = True

        self.fields["eori_number"].initial = self.EORI_INDIVIDUAL
        self.fields["eori_number"].disabled = True

    def clean(self):
        """Set type as individual as Importer can be an organisation too."""
        self.instance.type = Importer.INDIVIDUAL
        return super().clean()

    def clean_eori_number(self):
        """Make sure eori number equals GBPR."""
        if eori_number := self.cleaned_data.get("eori_number"):
            if not eori_number.lower() == self.EORI_INDIVIDUAL.lower():
                raise ValidationError(
                    f"'{eori_number}' must be set to {self.EORI_INDIVIDUAL} for individual importers."
                )

            return eori_number


class ImporterIndividualNonILBForm(ImporterIndividualForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in ["user", "eori_number"]:
            self.fields[key].disabled = True
            self.fields[key].help_text = "Contact ILB to update this field."


class ImporterOrganisationForm(forms.ModelForm):
    class Meta:
        model = Importer
        fields = [
            "name",
            "registered_number",
            "eori_number",
            "region_origin",
            "comments",
        ]
        widgets = {"name": forms.Textarea(attrs={"rows": 1})}

    class Media:
        js = ("web/js/api/check_company_number.js", "web/js/pages/edit-organisation.js")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True

        # Set in clean_registered_number if a company is found
        self.company = None

        # EORI number is required if it's already in the DB, or if it's a new importer
        if self.instance.eori_number or not self.instance.pk:
            self.fields["eori_number"].required = True

    def clean(self):
        """Set type as organisation as Importer can be an individual too."""
        self.instance.type = Importer.ORGANISATION
        return super().clean()

    def clean_registered_number(self) -> str | None:
        if registered_number := self.cleaned_data.get("registered_number"):
            # this is parsed in save()
            try:
                self.company = api_get_company(registered_number)
            except APIError as e:
                raise ValidationError(e.error_msg)
            except CompanyNotFound:
                self.company = None

            return registered_number

        return None

    def clean_eori_number(self):
        """Make sure eori number starts with GB."""
        if eori_number := self.cleaned_data.get("eori_number"):
            prefix = "GB"

            if not eori_number.lower().startswith(prefix.lower()):
                raise ValidationError(f"'{eori_number}' doesn't start with {prefix}")

            # Example value: GB123456789012345
            eori_number_length = len(eori_number[2:])

            if eori_number_length != 12 and eori_number_length != 15:
                raise ValidationError("Must start with 'GB' followed by 12 or 15 numbers")

            return eori_number

    def save(self, commit=True):
        instance = super().save(commit)

        # Creates an office if registered_number was set and returned a company.
        if commit and self.company:
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


class ImporterOrganisationNonILBForm(ImporterOrganisationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in ["registered_number", "name", "eori_number"]:
            self.fields[key].disabled = True
            self.fields[key].help_text = "Contact ILB to update this field."


class ImporterFilter(FilterSet):
    class AgentCharFilter(CharFilter):
        def filter(self, qs: QuerySet[Importer], value: str) -> QuerySet[Importer]:
            if not value:
                return qs

            return qs.filter(
                # Filter by the agent name
                (
                    Q(agents__name__icontains=value)
                    | Q(agents__user__title__icontains=value)
                    | Q(agents__user__first_name__icontains=value)
                    | Q(agents__user__last_name__icontains=value)
                ),
                # Only include active.
                agents__is_active=True,
            )

    importer_entity_type = ChoiceFilter(
        field_name="type",
        choices=Importer.TYPES,
        label="Importer Entity Type",
        empty_label="Any",
    )

    status = ChoiceFilter(
        field_name="is_active",
        choices=((True, "Current"), (False, "Archived")),
        lookup_expr="exact",
        label="Status",
        empty_label="Any",
    )

    name = CharFilter(lookup_expr="icontains", label="Importer Name", method="filter_importer_name")
    agent_name = AgentCharFilter(lookup_expr="icontains", label="Agent Name")

    @property
    def qs(self) -> QuerySet[Importer]:
        # Filter base queryset to only get importers that are not agents.
        return super().qs.filter(main_importer__isnull=True).distinct()

    def filter_importer_name(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(user__title__icontains=value)
            | Q(user__first_name__icontains=value)
            | Q(user__last_name__icontains=value)
        )

    class Meta:
        model = Importer
        fields: list[Any] = []


class AgentIndividualForm(forms.ModelForm):
    main_importer = forms.ModelChoiceField(
        queryset=Importer.objects.none(), label="Importer", disabled=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        importer = Importer.objects.filter(pk=self.initial["main_importer"])
        self.fields["main_importer"].queryset = importer
        self.fields["main_importer"].required = True
        self.fields["user"].required = True

    class Meta(ImporterIndividualForm.Meta):
        fields = ["main_importer", "user", "comments"]
        widgets = {"user": PersonWidget}

    def clean(self):
        self.instance.type = Importer.INDIVIDUAL
        return super().clean()


class AgentIndividualNonILBForm(AgentIndividualForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in ["user"]:
            self.fields[key].disabled = True
            self.fields[key].help_text = "Contact ILB to update this field."


class AgentOrganisationForm(forms.ModelForm):
    main_importer = forms.ModelChoiceField(
        queryset=Importer.objects.none(), label="Importer", disabled=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        importer = Importer.objects.filter(pk=self.initial["main_importer"])
        self.fields["main_importer"].queryset = importer
        self.fields["main_importer"].required = True
        self.fields["name"].required = True

    class Meta(ImporterOrganisationForm.Meta):
        fields = [
            "main_importer",
            "name",
            "registered_number",
            "comments",
        ]

        widgets = {"name": forms.Textarea(attrs={"rows": 1})}

    def clean(self):
        self.instance.type = Importer.ORGANISATION
        return super().clean()


class AgentOrganisationNonILBForm(AgentOrganisationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in ["name", "registered_number"]:
            self.fields[key].disabled = True
            self.fields[key].help_text = "Contact ILB to update this field."


# Needed for now because we don't want to show all permissions (everything but the agent)
def get_importer_object_permissions(
    importer: Importer,
) -> list[tuple[ImporterObjectPermissions, str]]:
    """Return object permissions for the Importer model with a label for each."""

    object_permissions = [
        (Perms.obj.importer.view, "View Applications / Licences"),
        (Perms.obj.importer.edit, "Edit Applications / Vary Licences"),
    ]

    # The agent should never have the manage_contacts_and_agents permission.
    if not importer.is_agent():
        object_permissions.append(
            (Perms.obj.importer.manage_contacts_and_agents, "Approve / Reject Agents and Importers")
        )

    return object_permissions


class ImporterUserObjectPermissionsForm(UserObjectPermissionsForm):
    obj: Importer

    def get_obj_perms_field_widget(self):
        return forms.CheckboxSelectMultiple(attrs={"class": "radio-relative"})

    def get_obj_perms_field_choices(self):
        # Only iterate over permissions we show in the main edit importer view
        return [(p.codename, label) for (p, label) in get_importer_object_permissions(self.obj)]


class ArchiveSection5AuthorityForm(forms.ModelForm):
    class Meta:
        model = Section5Authority
        fields = ["archive_reason", "other_archive_reason"]
        widgets = {"archive_reason": CheckboxSelectMultiple(choices=ArchiveReasonChoices.choices)}

    def clean(self):
        data = super().clean()

        if ArchiveReasonChoices.OTHER in data.get("archive_reason", []) and not data.get(
            "other_archive_reason"
        ):
            self.add_error("other_archive_reason", "You must enter this item.")

        return data
