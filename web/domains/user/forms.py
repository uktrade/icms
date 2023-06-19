from typing import Any

from django import forms
from django.forms.widgets import EmailInput, Select, Textarea
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, FilterSet

import web.views.utils.countries
from web.forms.fields import PhoneNumberField
from web.forms.widgets import DateInput
from web.models import AlternativeEmail, Email, PersonalEmail, PhoneNumber, User


class UserDetailsUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    class Meta:
        model = User

        fields = [
            "title",
            "first_name",
            "last_name",
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
            "date_of_birth": DateInput(),
            "work_address": Textarea({"rows": 5, "readonly": "readonly"}),
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


class PhoneNumberForm(forms.ModelForm):
    telephone_number = forms.CharField(validators=PhoneNumberField().validators)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telephone_number"].initial = self.instance.phone

    def clean_telephone_number(self):
        phone = self.cleaned_data["telephone_number"]
        self.instance.phone = phone
        return phone

    class Meta:
        model = PhoneNumber
        fields = ["telephone_number", "type", "comment"]
        widgets = {"type": Select(choices=PhoneNumber.TYPES)}


class AlternativeEmailsForm(forms.ModelForm):
    notifications = forms.CharField(
        required=False, widget=Select(choices=((True, "Yes"), (False, "No")))
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notifications"].initial = self.instance.portal_notifications

    def clean_notifications(self):
        response = self.cleaned_data.get("notifications", None)
        self.instance.portal_notifications = True if response else False
        return response

    class Meta:
        model = AlternativeEmail
        fields = ["email", "type", "notifications", "comment"]

        widgets = {
            "email": EmailInput(),
            "type": Select(choices=Email.TYPES),
        }


class PersonalEmailForm(forms.ModelForm):
    PRIMARY = "PRIMARY"
    notifications = forms.CharField(
        required=False, widget=Select(choices=((PRIMARY, "Primary"), (True, "Yes"), (False, "No")))
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.is_primary:
            self.fields["notifications"].initial = PersonalEmailForm.PRIMARY
        else:
            self.fields["notifications"].initial = self.instance.portal_notifications

    def clean_notifications(self):
        response = self.cleaned_data.get("notifications", None)
        self.instance.is_primary = True if response == PersonalEmailForm.PRIMARY else False
        self.instance.portal_notifications = True if response else False
        return response

    class Meta:
        model = PersonalEmail
        fields = ["email", "type", "notifications", "comment"]

        widgets = {
            "email": EmailInput(),
            "type": Select(choices=Email.TYPES),
        }


class PeopleFilter(FilterSet):
    email_address = CharFilter(
        field_name="personal_emails__email", lookup_expr="icontains", label="Email"
    )
    forename = CharFilter(field_name="first_name", lookup_expr="icontains", label="Forename")
    surname = CharFilter(field_name="last_name", lookup_expr="icontains", label="Surname")
    organisation = CharFilter(
        field_name="organisation", lookup_expr="icontains", label="Organisation"
    )
    department = CharFilter(field_name="department", lookup_expr="icontains", label="Department")
    job = CharFilter(field_name="job_title", lookup_expr="icontains", label="Job")

    class Meta:
        model = User
        fields: list[Any] = []


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


class PostCodeSearchForm(forms.Form):
    post_code = forms.CharField(required=True, label="Postcode")
    country = forms.CharField(
        required=False,
        widget=forms.Select(choices=web.views.utils.countries.get()),
        help_text="Choose a country to begin manually entering the address",
    )


class ManualAddressEntryForm(forms.Form):
    country = forms.CharField(widget=forms.TextInput({"readonly": "readonly"}))
    address = forms.CharField(max_length=4000, widget=forms.Textarea({"rows": 6, "cols": 50}))

    def clean_address(self):
        address = self.cleaned_data.get("address", "").upper()
        country = self.cleaned_data.get("country", "").upper()

        if country not in address:
            raise forms.ValidationError("Country name must be included in the address.")

        return address
