from django import forms
from django.conf import settings
from django.db.models import Q
from django_select2 import forms as s2forms

from web.domains.constabulary.models import Constabulary
from web.domains.file.models import File
from web.domains.file.utils import ICMSFileField
from web.domains.firearms.widgets import CheckboxSelectMultipleTable
from web.forms.widgets import DateInput
from web.models import (
    ConstabularyEmail,
    DFLApplication,
    ImportApplication,
    ImportContact,
    OpenIndividualLicenceApplication,
    UserImportCertificate,
)


class ConstabularyEmailForm(forms.ModelForm):
    status = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
    email_to = forms.ChoiceField(label="To", widget=s2forms.Select2Widget, choices=())
    email_cc_address_list = forms.CharField(
        required=False, label="Cc", help_text="Enter CC email addresses separated by a comma"
    )
    attachments = forms.ModelMultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultipleTable(attrs={"class": "radio-relative"}),
        queryset=File.objects.none(),
    )
    email_subject = forms.CharField(label="Subject")
    email_body = forms.CharField(label="Body", widget=forms.Textarea)

    class Meta:
        model = ConstabularyEmail
        fields = (
            "status",
            "email_to",
            "email_cc_address_list",
            "attachments",
            "email_subject",
            "email_body",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        self.fields["email_to"].choices = choices

        initial = [
            (settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL, settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL)
        ]
        self.fields["email_cc_address_list"].choices = initial + choices

        application = self.instance.import_application

        application_files_filter = self._get_file_filter(application)
        files = File.objects.filter(application_files_filter, is_active=True)

        self.fields["attachments"].queryset = files
        # set files and process on the widget to make them available in the widget's template
        self.fields["attachments"].widget.qs = files
        self.fields["attachments"].widget.process = application

    def _get_file_filter(self, application: ImportApplication) -> Q:

        process_type = application.process_type

        if process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
            return Q(firearmsauthority__verified_certificates__import_application=application) | Q(
                userimportcertificate__import_application=application
            )

        elif process_type == DFLApplication.PROCESS_TYPE:
            return Q(dflgoodscertificate__dfl_application=application)

        raise NotImplementedError(f"process_type: {application.process_type} not supported")


class ConstabularyEmailResponseForm(forms.ModelForm):
    class Meta:
        model = ConstabularyEmail
        fields = ("email_response",)


class ImportContactPersonForm(forms.ModelForm):
    last_name = forms.CharField(required=True, label="Surname")

    class Meta:
        model = ImportContact
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
        model = ImportContact
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


class UserImportCertificateForm(forms.ModelForm):
    document = ICMSFileField(required=True)

    certificate_type = forms.ChoiceField(
        choices=(UserImportCertificate.CertificateType.registered_as_choice(),)
    )

    class Meta:
        model = UserImportCertificate
        fields = (
            "reference",
            "certificate_type",
            "constabulary",
            "date_issued",
            "expiry_date",
            "document",
        )
        widgets = {"date_issued": DateInput, "expiry_date": DateInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.is_active:
            self.fields["document"].required = False

    def clean(self):
        data = super().clean()

        # document is handled in the view
        data.pop("document", None)
