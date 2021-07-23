from typing import TYPE_CHECKING

from django import forms
from guardian.shortcuts import get_users_with_perms

from web.domains.case._import.models import ImportApplication
from web.domains.case.export.models import ExportApplication
from web.domains.file.utils import ICMSFileField
from web.models import User

from .models import (
    CASE_NOTE_STATUSES,
    ApplicationBase,
    CaseNote,
    UpdateRequest,
    WithdrawApplication,
)
from .types import ImpOrExpT

if TYPE_CHECKING:
    from django.db.models import QuerySet


class DocumentForm(forms.Form):
    document = ICMSFileField(required=True)


class SubmitForm(forms.Form):
    confirmation = forms.CharField(
        label='Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]

        if confirmation != "I AGREE":
            raise forms.ValidationError("Please agree to the declaration of truth.")

        return confirmation


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


class ResponsePreparationBaseForm(forms.ModelForm):
    class Meta:
        fields = ("decision", "refuse_reason")
        widgets = {"refuse_reason": forms.Textarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["decision"].required = True

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get("decision") == ApplicationBase.REFUSE
            and cleaned_data.get("refuse_reason") == ""
        ):
            self.add_error("response", "This field is required when the Application is refused")


class ResponsePreparationImportForm(ResponsePreparationBaseForm):
    class Meta:
        model = ImportApplication
        fields = ResponsePreparationBaseForm.Meta.fields


class ResponsePreparationExportForm(ResponsePreparationBaseForm):
    class Meta:
        model = ExportApplication
        fields = ResponsePreparationBaseForm.Meta.fields


def application_contacts(application: ImpOrExpT) -> "QuerySet[User]":
    if isinstance(application, ImportApplication):
        if application.agent:
            users = get_users_with_perms(
                application.agent, only_with_perms_in=["is_contact_of_importer"]
            )
        else:
            users = get_users_with_perms(
                application.importer, only_with_perms_in=["is_contact_of_importer"]
            )
    elif isinstance(application, ExportApplication):
        if application.agent:
            users = get_users_with_perms(
                application.agent, only_with_perms_in=["is_contact_of_exporter"]
            )
        else:
            users = get_users_with_perms(
                application.exporter, only_with_perms_in=["is_contact_of_exporter"]
            )
    else:
        raise Exception("Application not supported: {}".format(application))

    return users.filter(is_active=True)
