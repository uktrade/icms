from django import forms
from django_select2.forms import ModelSelect2Widget
from guardian.shortcuts import get_objects_for_user

from web.domains.case._import.models import (
    ImportApplicationType,
    OpenIndividualLicenceApplication,
)
from web.domains.importer.models import Importer
from web.domains.office.models import Office


class CreateOILForm(forms.ModelForm):
    importer = forms.ModelChoiceField(
        queryset=Importer.objects.none(),
        label="Main Importer",
        widget=ModelSelect2Widget(
            search_fields=(
                "name__icontains",
                "user__first_name__icontains",
                "user__last_name__icontains",
            )
        ),
    )
    importer_office = forms.ModelChoiceField(
        queryset=Office.objects.none(),
        label="Importer Office",
        widget=ModelSelect2Widget(
            search_fields=("postcode__icontains", "address__icontains"),
            dependent_fields={"importer": "importer"},
        ),
    )

    class Meta:
        model = OpenIndividualLicenceApplication
        fields = ("importer", "importer_office")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        active_importers = Importer.objects.filter(is_active=True)
        importers = get_objects_for_user(
            user,
            ["web.is_contact_of_importer", "web.is_agent_of_importer"],
            active_importers,
            any_perm=True,
            with_superuser=True,
        )
        self.fields["importer"].queryset = importers
        self.fields["importer_office"].queryset = Office.objects.filter(
            is_active=True, importer__in=importers
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        application_type = ImportApplicationType.objects.filter(
            is_active=True, sub_type=ImportApplicationType.SUBTYPE_OPEN_INDIVIDUAL_LICENCE
        ).first()
        instance.application_type = application_type
        if commit:
            instance.save()
            self.save_m2m()
        return instance
