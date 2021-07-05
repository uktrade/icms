from django import forms

from web.domains.file.utils import ICMSFileField
from web.domains.user.models import User

from . import models


class EditSPSForm(forms.ModelForm):
    class Meta:
        model = models.PriorSurveillanceApplication
        fields = ("contact", "applicant_reference")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: ICMSLST-425 filter users here correctly (users with access to the importer)
        self.fields["contact"].queryset = User.objects.all()


class AddContractDocumentForm(forms.ModelForm):
    document = ICMSFileField(required=True)

    class Meta:
        model = models.PriorSurveillanceContractFile
        fields = ("file_type",)


class EditContractDocumentForm(forms.ModelForm):
    class Meta:
        model = models.PriorSurveillanceContractFile

        fields = ("file_type",)
