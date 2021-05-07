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


class WithdrawForm(forms.ModelForm):
    class Meta:
        model = models.WithdrawImportApplication
        fields = ("reason",)


class WithdrawResponseForm(forms.ModelForm):
    STATUSES = (
        models.WithdrawImportApplication.ACCEPTED,
        models.WithdrawImportApplication.REJECTED,
    )
    status = forms.ChoiceField(label="Withdraw Decision", choices=STATUSES)
    response = forms.CharField(
        required=False, label="Withdraw Reject Reason", widget=forms.Textarea
    )

    class Meta:
        model = models.WithdrawImportApplication
        fields = (
            "status",
            "response",
        )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("status") == models.WithdrawImportApplication.STATUS_REJECTED
            and cleaned_data.get("response") == ""
        ):
            self.add_error("response", "This field is required when Withdrawal is refused")


class ResponsePreparationForm(forms.ModelForm):
    class Meta:
        model = models.ImportApplication
        fields = ("decision", "refuse_reason")
        widgets = {"refuse_reason": forms.Textarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["decision"].required = True

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("decision") == models.ImportApplication.REFUSE
            and cleaned_data.get("refuse_reason") == ""
        ):
            self.add_error("response", "This field is required when the Application is refused")


class CoverLetterForm(forms.ModelForm):
    class Meta:
        model = models.ImportApplication
        fields = ("cover_letter",)
        widgets = {"cover_letter": forms.Textarea(attrs={"lang": "html"})}


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


class ImportContactPersonForm(forms.ModelForm):
    last_name = forms.CharField(required=True, label="Surname")

    class Meta:
        model = models.ImportContact
        fields = (
            "first_name",
            "last_name",
            "street",
            "city",
            "postcode",
            "region",
            "country",
            "dealer",
        )
        labels = {
            "first_name": "First Name",
            "last_name": "Surname",
            "dealer": "Did you buy from a dealer?",
        }


class ImportContactLegalEntityForm(forms.ModelForm):
    class Meta:
        model = models.ImportContact
        fields = (
            "first_name",
            "registration_number",
            "street",
            "city",
            "postcode",
            "region",
            "country",
            "dealer",
        )
        labels = {
            "first_name": "Name of Legal Person",
            "registration_number": "Registration Number",
            "dealer": "Did you buy from a dealer?",
        }
