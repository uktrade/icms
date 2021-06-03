from typing import Any, Dict, Optional

from django import forms
from django.utils import timezone
from django_select2.forms import ModelSelect2Widget
from guardian.shortcuts import get_objects_for_user

from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.template.models import Template
from web.forms.widgets import DateInput

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

    def __init__(self, *args: Any, user: models.User, **kwargs: Any) -> None:
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


class CreateWoodQuotaApplicationForm(CreateImportApplicationForm):
    """Create wood quota application form - Defines extra validation logic"""

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()

        if not self.has_error("importer_office"):
            office: Office = cleaned_data["importer_office"]
            postcode: Optional[str] = office.postcode

            if not postcode or (not postcode.upper().startswith("BT")):
                self.add_error(
                    "importer_office",
                    "Wood applications can only be made for Northern Ireland traders.",
                )

        return cleaned_data


class CoverLetterForm(forms.ModelForm):
    class Meta:
        model = models.ImportApplication
        fields = ("cover_letter",)
        widgets = {"cover_letter": forms.Textarea(attrs={"lang": "html"})}


# TODO Extend this form and include `issue_paper_licence_only` when required
class LicenceDateForm(forms.ModelForm):
    licence_start_date = forms.DateField(
        required=True, label="Licence Start Date", widget=DateInput
    )
    licence_end_date = forms.DateField(required=True, label="Licence End Date", widget=DateInput)

    class Meta:
        model = models.ImportApplication
        fields = ("licence_start_date", "licence_end_date")

    def clean(self):
        data = super().clean()
        start_date = data.get("licence_start_date")
        end_date = data.get("licence_end_date")
        if not start_date or not end_date:
            return
        today = timezone.now().date()

        if start_date < today:
            self.add_error("licence_start_date", "Date must be in the future.")
        if start_date > end_date:
            self.add_error("licence_end_date", "End Date must be after Start Date.")


class EndorsementChoiceImportApplicationForm(forms.ModelForm):
    content = forms.ModelChoiceField(
        queryset=Template.objects.filter(is_active=True, template_type=Template.ENDORSEMENT)
    )

    class Meta:
        model = models.EndorsementImportApplication
        fields = ("content",)

    def clean_content(self):
        endorsement = self.cleaned_data["content"]
        return endorsement.template_content


class EndorsementImportApplicationForm(forms.ModelForm):
    class Meta:
        model = models.EndorsementImportApplication
        fields = ("content",)


class ChecklistBaseForm(forms.ModelForm):
    class Meta:
        fields = (
            "case_update",
            "fir_required",
            "response_preparation",
            "validity_period_correct",
            "endorsements_listed",
            "authorisation",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change checklist fields to required (e.g. only selected is valid)
        for field in ["response_preparation", "authorisation"]:
            self.fields[field].required = True
