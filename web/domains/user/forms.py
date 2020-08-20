from django.forms.fields import CharField
from django.forms.widgets import (
    CheckboxInput,
    CheckboxSelectMultiple,
    EmailInput,
    PasswordInput,
    Select,
    Textarea,
)
from django.utils.translation import gettext_lazy as _
from django_filters import BooleanFilter, CharFilter, MultipleChoiceFilter
from web.forms import ModelEditForm, ModelSearchFilter, validators
from web.forms.fields import PhoneNumberField
from web.forms.widgets import DateInput

from .models import AlternativeEmail, Email, PersonalEmail, PhoneNumber, User


class UserDetailsUpdateForm(ModelEditForm):
    security_answer_repeat = CharField(
        required=True, label="Re-enter Security Answer", widget=PasswordInput(render_value=True)
    )

    def __init__(self, *args, **kwargs):
        super(UserDetailsUpdateForm, self).__init__(*args, **kwargs)
        self.fields["security_answer_repeat"].initial = self.instance.security_answer
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_security_answer_repeat(self):
        return validators.validate_security_answer_confirmation(self)

    class Meta:
        model = User

        fields = [
            "title",
            "first_name",
            "preferred_first_name",
            "middle_initials",
            "last_name",
            "organisation",
            "department",
            "job_title",
            "location_at_address",
            "work_address",
            "share_contact_details",
            "date_of_birth",
            "security_question",
            "security_answer",
        ]

        labels = {
            "first_name": "Forename",
            "preferred_first_name": "Preferred Forename",
            "last_name": "Surname",
            "organisation": "Organisation Name (Employer)",
            "department": "Department Name (Employer)",
            "job_title": "Job Title (Employer)",
            "share_contact_details": "Share Contact Deails?",
            "location_at_address": "Floor/Room/Bay/Location",
            "work_address": "Work Address",
        }
        widgets = {
            "share_contact_details": Select(choices=((False, "No"), (True, "Yes"))),
            "security_question": Textarea({"rows": 2}),
            "security_answer": PasswordInput(render_value=True),
            "location_at_address": Textarea({"rows": 2, "cols": 50}),
            "date_of_birth": DateInput(),
            "work_address": Textarea({"rows": 5, "readonly": "readonly"}),
        }

        help_texts = {
            "title": "Preferred form of address. Examples: Mr, Ms, Miss, Mrs, Dr, Rev, etc.",  # NOQA
            "first_name": "Formal given name",
            "preferred_first_name": "Preferred forename can be left blank. \
                It is not used on formal document. \
                Example Forename(Preferred): Robert (Bob)",
            "middle_initials": "Initials of middle names (if used)",
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


class PhoneNumberForm(ModelEditForm):
    telephone_number = CharField(validators=PhoneNumberField().validators)

    def __init__(self, *args, **kwargs):
        super(PhoneNumberForm, self).__init__(*args, **kwargs)
        self.fields["telephone_number"].initial = self.instance.phone

    def clean_telephone_number(self):
        phone = self.cleaned_data["telephone_number"]
        self.instance.phone = phone
        return phone

    class Meta:
        model = PhoneNumber
        fields = ["telephone_number", "type", "comment"]
        widgets = {"type": Select(choices=PhoneNumber.TYPES)}


class AlternativeEmailsForm(ModelEditForm):
    notifications = CharField(required=False, widget=Select(choices=((True, "Yes"), (False, "No"))))

    def __init__(self, *args, **kwargs):
        super(AlternativeEmailsForm, self).__init__(*args, **kwargs)
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


class PersonalEmailForm(ModelEditForm):
    PRIMARY = "PRIMARY"
    notifications = CharField(
        required=False, widget=Select(choices=((PRIMARY, "Primary"), (True, "Yes"), (False, "No")))
    )

    def __init__(self, *args, **kwargs):
        super(PersonalEmailForm, self).__init__(*args, **kwargs)
        if self.instance.is_primary:
            self.fields["notifications"].initial = PersonalEmailForm.PRIMARY
        else:
            self.fields["notifications"].initial = self.instance.portal_notifications

    def clean_notifications(self):
        response = self.cleaned_data.get("notifications", None)
        self.instance.is_primary = True if response == PersonalEmailForm.PRIMARY else False
        self.instance.portal_notifications = True if response else False
        return response

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.is_primary:
            instance.user.username = instance.email
            instance.user.email = instance.email
            instance.user.save()
        if commit:
            instance.save()

        return instance

    class Meta:
        model = PersonalEmail
        fields = ["email", "type", "notifications", "comment"]

        widgets = {
            "email": EmailInput(),
            "type": Select(choices=Email.TYPES),
        }


class PeopleFilter(ModelSearchFilter):
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
        fields = []


class UserListFilter(ModelSearchFilter):
    email_address = CharFilter(field_name="email", lookup_expr="icontains", label="Email Address")
    username = CharFilter(field_name="username", lookup_expr="icontains", label="Login Name")
    forename = CharFilter(field_name="first_name", lookup_expr="icontains", label="Forename")
    surname = CharFilter(field_name="last_name", lookup_expr="icontains", label="Surname")
    organisation = CharFilter(
        field_name="organisation", lookup_expr="icontains", label="Organisation"
    )
    job_title = CharFilter(field_name="job_title", lookup_expr="icontains", label="Job Title")
    status = MultipleChoiceFilter(
        field_name="account_status",
        lookup_expr="icontains",
        label="Account Status",
        choices=User.STATUSES,
        widget=CheckboxSelectMultiple,
    )
    password_disposition = BooleanFilter(
        field_name="password_disposition",
        lookup_expr="icontains",
        widget=CheckboxInput,
        method="filter_password_disposition",
        label="Disposition",
    )

    def filter_password_disposition(self, queryset, name, value):
        if value:
            return queryset.filter(password_disposition=User.TEMPORARY)
        else:
            return queryset

    class Meta:
        model = User
        fields = []
