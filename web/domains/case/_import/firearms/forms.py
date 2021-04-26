from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django_select2 import forms as s2forms

from web.domains.case._import.models import ImportContact
from web.domains.constabulary.models import Constabulary
from web.domains.country.models import Country
from web.domains.file.models import File
from web.domains.firearms.widgets import CheckboxSelectMultipleTable
from web.domains.user.models import User
from web.forms.widgets import DateInput

from . import models


class PrepareOILForm(forms.ModelForm):
    applicant_reference = forms.CharField(
        label="Applicant's Reference",
        help_text="Enter your own reference for this application.",
        required=False,
    )
    contact = forms.ModelChoiceField(
        queryset=User.objects.all(),
        help_text="Select the main point of contact for the case. This will usually be the person who created the application.",
    )
    commodity_code = forms.ChoiceField(
        label="Commodity Code",
        help_text="""
            You must pick the commodity code group that applies to the items that you wish to
            import. Please note that "ex Chapter 97" is only relevant to collectors pieces and
            items over 100 years old. Please contact HMRC classification advisory service,
            01702 366077, if you are unsure of the correct code.
        """,
        choices=[(x, x) for x in [None, "ex Chapter 93", "ex Chapter 95"]],
    )
    origin_country = forms.ModelChoiceField(
        label="Country Of Origin",
        empty_label=None,
        queryset=Country.objects.filter(name="Any Country"),
    )
    consignment_country = forms.ModelChoiceField(
        label="Country Of Consignment",
        empty_label=None,
        queryset=Country.objects.filter(name="Any Country"),
    )
    section1 = forms.BooleanField(disabled=True, label="Firearms Licence for")
    section2 = forms.BooleanField(disabled=True, label="")

    class Meta:
        model = models.OpenIndividualLicenceApplication
        fields = (
            "contact",
            "applicant_reference",
            "section1",
            "section2",
            "origin_country",
            "consignment_country",
            "commodity_code",
            "know_bought_from",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["know_bought_from"].required = True


class UserImportCertificateForm(forms.ModelForm):
    document = forms.FileField(required=True, widget=forms.ClearableFileInput())
    certificate_type = forms.ChoiceField(choices=(models.UserImportCertificate.REGISTERED,))

    class Meta:
        model = models.UserImportCertificate
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
        if self.instance.pk and self.instance.files.active().exists():
            self.fields["document"].required = False

    def clean(self):
        data = super().clean()

        # document is handled in the view
        data.pop("document", None)


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


class SubmitOILForm(forms.Form):
    confirmation = forms.CharField(
        label='Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]

        if confirmation != "I AGREE":
            raise ValidationError("Please agree to the declaration of truth.")

        return confirmation


class ChecklistFirearmsOILApplicationForm(forms.ModelForm):
    class Meta:
        model = models.ChecklistFirearmsOILApplication
        fields = (
            "authority_required",
            "authority_received",
            "authority_police",
            "case_update",
            "fir_required",
            "response_preparation",
            "validity_match",
            "endorsements_listed",
            "authorisation",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = True


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
        model = models.ConstabularyEmail
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

        files = File.objects.filter(
            Q(
                firearmsauthority__verified_certificates__import_application=self.instance.application
            )
            | Q(userimportcertificate__import_application=self.instance.application)
        ).filter(is_active=True)
        self.fields["attachments"].queryset = files
        # set files and process on the widget to make them available in the widget's template
        self.fields["attachments"].widget.qs = files
        self.fields["attachments"].widget.process = self.instance.application


class ConstabularyEmailResponseForm(forms.ModelForm):
    class Meta:
        model = models.ConstabularyEmail
        fields = ("email_response",)
