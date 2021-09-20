from django import forms

from web.domains.file.utils import ICMSFileField
from web.forms.widgets import DateInput

from .models import ImportContact, SupplementaryReport, UserImportCertificate
from .types import FaImportApplication


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

    def __init__(self, *args, application, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.is_active:
            self.fields["document"].required = False

        if application.process_type == "OpenIndividualLicenceApplication":
            self.fields["certificate_type"].choices = (
                UserImportCertificate.CertificateType.registered_as_choice(),
            )


class SupplementaryReportForm(forms.ModelForm):
    class Meta:
        model = SupplementaryReport
        fields = ("transport", "date_received", "bought_from")
        widgets = {"date_received": DateInput}

    def __init__(self, *args, application: FaImportApplication, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.fields["bought_from"].queryset = application.importcontact_set.all()
