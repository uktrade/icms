from typing import Any

from django import forms
from django.forms.widgets import EmailInput, Select, Textarea
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, ChoiceFilter, FilterSet

from web.forms.fields import JqueryDateField, PhoneNumberField
from web.forms.widgets import ICMSModelSelect2Widget, YesNoRadioSelectInline
from web.models import Email, Exporter, Importer, PhoneNumber, User
from web.one_login.constants import ONE_LOGIN_UNSET_NAME


class OneLoginNewUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]

    def __init__(self, *args: Any, initial: dict[str, Any], instance: User, **kwargs: Any) -> None:
        """Form used to get new users to provide their name.

        The first_name and last_name of users coming from GOV.UK One Login will be set to
        "one_login_unset".
        For that scenario that form sets the initial value to "".
        """

        one_login_default_name = ONE_LOGIN_UNSET_NAME.casefold()

        if instance.first_name.casefold() == one_login_default_name:
            initial |= {"first_name": ""}

        if instance.last_name.casefold() == one_login_default_name:
            initial |= {"last_name": ""}

        super().__init__(*args, initial=initial, instance=instance, **kwargs)

        self.fields["first_name"].required = True
        self.fields["last_name"].required = True


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
    is_active = ChoiceFilter(
        field_name="is_active",
        choices=((True, "Yes"), (False, "No")),
        lookup_expr="exact",
        label="Is Active",
        empty_label="Any",
    )

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


class UserManagementEmailForm(forms.Form):
    subject = forms.CharField(max_length=100, label="Subject")
    body = forms.CharField(widget=forms.Textarea, label="Body")
    send_email = forms.BooleanField(required=False)


class ImporterWidget(ICMSModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "registered_number__icontains",
        "eori_number__icontains",
        "user__first_name__icontains",
        "user__email__icontains",
    ]

    def label_from_instance(self, importer: Importer) -> str:
        return importer.display_name


class ExporterWidget(ICMSModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "registered_number__icontains",
    ]

    def label_from_instance(self, exporter: Exporter) -> str:
        return exporter.name


class OneLoginTestAccountsCreateForm(forms.Form):
    user_email = forms.EmailField(help_text="Enter the email address of the user you want to setup")

    importer = forms.ModelChoiceField(
        label="Importer",
        help_text=(
            "Search an importer to link."
            " Importers returned are matched against name, registerer number"
            ", eori number and user name/email."
        ),
        queryset=Importer.objects.filter(is_active=True, main_importer__isnull=True),
        widget=ImporterWidget,
        required=False,
    )

    importer_agent = forms.ModelChoiceField(
        label="Agent Importer",
        help_text=(
            "Search an agent importer to link."
            " Importers returned are matched against name, registerer number"
            ", eori number and user name/email."
        ),
        queryset=Importer.objects.filter(is_active=True, main_importer__isnull=False),
        widget=ImporterWidget,
        required=False,
    )

    exporter = forms.ModelChoiceField(
        label="Exporter",
        help_text=(
            "Search an exporter to link."
            " Exporters returned are matched against name and registerer number."
        ),
        queryset=Exporter.objects.filter(is_active=True, main_exporter__isnull=True),
        widget=ExporterWidget,
        required=False,
    )

    exporter_agent = forms.ModelChoiceField(
        label="Agent Exporter",
        help_text=(
            "Search an agent exporter to link."
            " Exporters returned are matched against name and registerer number."
        ),
        queryset=Exporter.objects.filter(is_active=True, main_exporter__isnull=False),
        widget=ExporterWidget,
        required=False,
    )

    def clean_user_email(self) -> str:
        email = self.cleaned_data["user_email"]

        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("User must exist before test accounts can be created.")

        return email.lower()

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        fields = ["importer", "importer_agent", "exporter", "exporter_agent"]
        if not any([cleaned_data.get(f) for f in fields]):
            self.add_error(None, "At least one link must be provided.")

        return cleaned_data
