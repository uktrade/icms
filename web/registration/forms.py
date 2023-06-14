from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UsernameField

from web.forms.fields import PhoneNumberField
from web.forms.widgets import DateInput
from web.models import PersonalEmail, User


class UserCreationForm(BaseUserCreationForm):
    telephone_number = PhoneNumberField()

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
            "date_of_birth": "Date of Birth",
        }

        widgets = {
            "date_of_birth": DateInput(),
        }

        field_classes = {"username": UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = True

    def save(self, commit=True):
        user = super().save(commit=True)

        PersonalEmail(
            user=user, email=user.email, is_primary=True, portal_notifications=True
        ).save()

        user.phone_numbers.create(phone=self.cleaned_data["telephone_number"])
