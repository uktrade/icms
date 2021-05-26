from django import forms

from web.domains.user.models import User

from . import models


# TODO: ICMSLST-593 implement
class EditOutwardProcessingTradeForm(forms.ModelForm):
    # TODO: filter users here correctly (users with access to the importer)
    contact = forms.ModelChoiceField(
        queryset=User.objects.all(),
        help_text="Select the main point of contact for the case. This will usually be the person who created the application.",
    )

    class Meta:
        model = models.OutwardProcessingTradeApplication
        fields = (
            "contact",
            "applicant_reference",
        )


class SubmitOutwardProcessingTradeForm(forms.Form):
    confirmation = forms.CharField(
        label='Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]

        if confirmation != "I AGREE":
            raise forms.ValidationError("Please agree to the declaration of truth.")

        return confirmation
