from django import forms
from django_select2.forms import ModelSelect2Widget
from guardian.shortcuts import get_objects_for_user

from web.domains.importer.models import Importer
from web.domains.office.models import Office

from . import models


class CreateImportApplicationForm(forms.Form):
    importer = forms.ModelChoiceField(
        queryset=Importer.objects.none(),
        label="Main Importer",
        widget=ModelSelect2Widget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Select Importer",
            },
            search_fields=(
                "name__icontains",
                "user__first_name__icontains",
                "user__last_name__icontains",
            ),
        ),
    )
    importer_office = forms.ModelChoiceField(
        queryset=Office.objects.none(),
        label="Importer Office",
        widget=ModelSelect2Widget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Select Office",
            },
            search_fields=("postcode__icontains", "address__icontains"),
            dependent_fields={"importer": "importer"},
        ),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        active_importers = Importer.objects.filter(is_active=True, main_importer__isnull=True)
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


class WithdrawForm(forms.ModelForm):
    class Meta:
        model = models.WithdrawImportApplication
        fields = ("reason",)
