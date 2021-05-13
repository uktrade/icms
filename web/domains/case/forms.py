from django import forms

from web.domains.case.models import (
    CASE_NOTE_STATUSES,
    CaseNote,
    UpdateRequest,
    WithdrawApplication,
)
from web.domains.file.utils import ICMSFileField


class DocumentForm(forms.Form):
    document = ICMSFileField(required=True)


class CaseNoteForm(forms.ModelForm):
    status = forms.ChoiceField(choices=CASE_NOTE_STATUSES)

    class Meta:
        model = CaseNote
        fields = ["status", "note"]


class CloseCaseForm(forms.Form):
    send_email = forms.BooleanField(
        required=False,
        label="Send Email to Applicants?",
        help_text="This email can be edited from the templates management screens.",
        widget=forms.CheckboxInput(),
    )


class UpdateRequestForm(forms.ModelForm):
    class Meta:
        model = UpdateRequest
        fields = ("request_subject", "email_cc_address_list", "request_detail")


class WithdrawForm(forms.ModelForm):
    class Meta:
        model = WithdrawApplication
        fields = ("reason",)


class WithdrawResponseForm(forms.ModelForm):
    STATUSES = (WithdrawApplication.ACCEPTED, WithdrawApplication.REJECTED)

    status = forms.ChoiceField(label="Withdraw Decision", choices=STATUSES)
    response = forms.CharField(
        required=False, label="Withdraw Reject Reason", widget=forms.Textarea
    )

    class Meta:
        model = WithdrawApplication
        fields = (
            "status",
            "response",
        )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("status") == WithdrawApplication.STATUS_REJECTED
            and cleaned_data.get("response") == ""
        ):
            self.add_error("response", "This field is required when Withdrawal is refused")
