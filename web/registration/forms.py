from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UsernameField
from django.core.exceptions import ObjectDoesNotExist

from web.auth.utils import get_legacy_user_by_username
from web.forms.fields import JqueryDateField, PhoneNumberField
from web.models import Email, User


class UserCreationForm(BaseUserCreationForm):
    telephone_number = PhoneNumberField()
    date_of_birth = JqueryDateField(required=False, label="Date of Birth")

    class Meta:
        model = User
        fields = BaseUserCreationForm.Meta.fields + (
            "email",
            "title",
            "first_name",
            "last_name",
            "telephone_number",
            "organisation",
            "date_of_birth",
        )

        labels = {
            "organisation": "Organisation Name (Employer)",
            "email": "Email",
            "first_name": "Forename",
            "last_name": "Surname",
            "telephone_number": "Telephone Number",
        }

        field_classes = {"username": UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = True

    def save(self, commit=True):
        user = super().save(commit=True)

        Email(user=user, email=user.email, is_primary=True, portal_notifications=True).save()

        user.phone_numbers.create(phone=self.cleaned_data["telephone_number"])


class AccountRecoveryForm(forms.Form):
    legacy_email = forms.EmailField(label="Email / Username")
    legacy_password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    # Raise the same error message regardless of the error
    FORM_ERROR = forms.ValidationError("Your username and password didn't match. Please try again.")

    def clean(self):
        cleaned_data = super().clean()

        legacy_email = cleaned_data.get("legacy_email")
        legacy_password = cleaned_data.get("legacy_password")

        if not legacy_email or not legacy_password:
            # Not fully valid so return
            return cleaned_data

        try:
            user = get_legacy_user_by_username(legacy_email)
        except ObjectDoesNotExist:
            raise self.FORM_ERROR

        if not user.check_password(legacy_password):
            raise self.FORM_ERROR

        # Store the user to update
        cleaned_data["legacy_user"] = user

        return cleaned_data
