from django import forms

from web.domains.file.utils import ICMSFileField
from web.forms.fields import JqueryDateField
from web.forms.widgets import YesNoRadioSelectInline

from .models import ImportContact, UserImportCertificate
from .types import FaImportApplication


class ImportContactKnowBoughtFromForm(forms.Form):
    know_bought_from = forms.NullBooleanField(
        label="Do you know who you plan to buy/obtain these items from?",
        widget=YesNoRadioSelectInline,
    )

    def __init__(self, *args, application: FaImportApplication, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = application

    def clean_know_bought_from(self):
        bought_from = self.cleaned_data["know_bought_from"]

        if bought_from is None:
            raise forms.ValidationError("This field is required.")

        if bought_from is False and self.app.importcontact_set.exists():
            raise forms.ValidationError("Please remove contacts before setting this to No.")

        return bought_from


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
            "first_name": "First Name",  # /PS-IGNORE
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

    date_issued = JqueryDateField(required=True, label="Date Issued")
    expiry_date = JqueryDateField(required=True, label="Expiry Date")

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

    def __init__(self, *args, application, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.is_active:
            self.fields["document"].required = False

        if application.process_type == "OpenIndividualLicenceApplication":
            self.fields["certificate_type"].choices = (
                UserImportCertificate.CertificateType.registered_as_choice(),
            )
