from django import forms

from . import models


# TODO: ICMSLST-593 implement
class EditOutwardProcessingTradeForm(forms.ModelForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication
        fields = ("contact",)


class SubmitOutwardProcessingTradeForm(forms.Form):
    confirmation = forms.CharField(
        label='Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]

        if confirmation != "I AGREE":
            raise forms.ValidationError("Please agree to the declaration of truth.")

        return confirmation
