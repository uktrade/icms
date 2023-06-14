from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UsernameField

from web.models import PersonalEmail, User


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = (
            # TODO: Clean the username field. (A user with that username already exists.)
            "username",
            "email",
            "first_name",
            "last_name",
        )
        field_classes = {"username": UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = True

    def save(self, commit=True):
        user = super().save(commit=True)

        # Don't have access to this:
        # user.phone_numbers.create(phone=form.cleaned_data["telephone_number"])

        PersonalEmail(
            user=user, email=user.email, is_primary=True, portal_notifications=True
        ).save()
