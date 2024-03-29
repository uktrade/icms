from typing import Any

from django import forms
from django.forms.widgets import EmailInput, Select, Textarea
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, FilterSet

from web.forms.fields import JqueryDateField, PhoneNumberField
from web.forms.widgets import YesNoRadioSelectInline
from web.models import Email, PhoneNumber, User


class UserDetailsUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    date_of_birth = JqueryDateField(required=False)
    email = forms.CharField(
        disabled=True, label="Account Email", help_text="Address used to log in to the service."
    )

    class Meta:
        model = User

        fields = [
            "title",
            "first_name",
            "last_name",
            "email",
            "organisation",
            "department",
            "job_title",
            "location_at_address",
            "work_address",
            "date_of_birth",
        ]

        labels = {
            "first_name": "Forename",
            "last_name": "Surname",
            "organisation": "Organisation Name (Employer)",
            "department": "Department Name (Employer)",
            "job_title": "Job Title (Employer)",
            "location_at_address": "Floor/Room/Bay/Location",
            "work_address": "Work Address",
        }
        widgets = {
            "location_at_address": Textarea({"rows": 2, "cols": 50}),
            "work_address": Textarea({"rows": 5}),
        }

        help_texts = {
            "title": "Preferred form of address. Examples: Mr, Ms, Miss, Mrs, Dr, Rev, etc.",  # NOQA
            "first_name": "Formal given name",
            "last_name": "Family or marriage name",
            "organisation": "Organisation name of direct employer. \
                This is not the names of organisations which work may be \
                carried out on behalf of, as this information is recorded \
                elsewhere on the system.",
            "department": "Department name associated with, within direct employing \
                organisation.",
            "job_title": "Job title used within direct employing organisation.",
            "location_at_address": _(
                "Room or bay number and location within the formal postal address below.\
             \nExample:\nROOM 104\nFIRST FLOOR REAR ANNEX"
            ),
            "work_address": _("Edit work address"),
        }


class UserListFilter(FilterSet):
    email_address = CharFilter(field_name="email", lookup_expr="icontains", label="Email Address")
    username = CharFilter(field_name="username", lookup_expr="icontains", label="Login Name")
    forename = CharFilter(field_name="first_name", lookup_expr="icontains", label="Forename")
    surname = CharFilter(field_name="last_name", lookup_expr="icontains", label="Surname")
    organisation = CharFilter(
        field_name="organisation", lookup_expr="icontains", label="Organisation"
    )
    job_title = CharFilter(field_name="job_title", lookup_expr="icontains", label="Job Title")

    class Meta:
        model = User
        fields: list[Any] = []


class UserPhoneNumberForm(forms.ModelForm):
    phone = forms.CharField(validators=PhoneNumberField().validators, label="Telephone Number")

    class Meta:
        model = PhoneNumber
        fields = ["phone", "type", "comment"]
        widgets = {"type": Select(choices=PhoneNumber.TYPES)}


class UserEmailForm(forms.ModelForm):
    class Meta:
        model = Email
        fields = ["email", "type", "comment", "portal_notifications", "is_primary"]
        labels = {
            "email": "Email Address",
            "type": "Type",
            "notifications": "Portal Notifications",
            "comment": "Comment",
        }
        widgets = {
            "email": EmailInput(),
            "type": Select(choices=Email.TYPES),
            "portal_notifications": YesNoRadioSelectInline,
            "is_primary": YesNoRadioSelectInline,
        }

        labels = {
            "portal_notifications": "Portal Notifications",
            "is_primary": "Primary Email",
        }
        help_texts = {
            "portal_notifications": "Set to Yes if you would like to be notified at this address",
            "is_primary": "Preferred contact address",
        }

    def save(self, commit=True):
        email = super().save(commit=True)

        # Extra logic to ensure there is always one primary email.
        previous_primary = email.user.emails.filter(is_primary=True).exclude(pk=email.pk).first()

        # Set old primary email to False
        if email.is_primary and previous_primary:
            previous_primary.is_primary = False
            previous_primary.save()

        # Set the form instance email to primary if one doesn't already exist.
        elif not email.is_primary and not previous_primary:
            email.is_primary = True

            if commit:
                email.save()

        return email
