from typing import Any

from django import forms
from django.db.models import QuerySet
from django_select2 import forms as s2forms

from web.domains.case.widgets import CheckboxSelectMultipleTable
from web.domains.file.utils import ICMSFileField
from web.forms.fields import JqueryDateField
from web.forms.mixins import OptionalFormMixin
from web.models import ExportApplication, ImportApplication, User
from web.permissions import get_all_case_officers, organisation_get_contacts

from .models import (
    ApplicationBase,
    CaseEmail,
    CaseNote,
    UpdateRequest,
    VariationRequest,
    WithdrawApplication,
)
from .types import CaseEmailConfig, ImpOrExp


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
    class Meta:
        model = CaseNote
        fields = ["note"]


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
        fields = ("request_subject", "request_detail")


class UpdateRequestResponseForm(forms.ModelForm):
    class Meta:
        model = UpdateRequest
        fields = ("response_detail",)


class WithdrawForm(forms.ModelForm):
    class Meta:
        model = WithdrawApplication
        fields = ("reason",)


class WithdrawResponseForm(forms.ModelForm):
    WITHDRAW_STATUSES = [
        ("", "--------"),
        (WithdrawApplication.Statuses.ACCEPTED, "Accepted"),
        (WithdrawApplication.Statuses.REJECTED, "Rejected"),
    ]

    status = forms.ChoiceField(label="Withdraw Decision", choices=WITHDRAW_STATUSES)
    response = forms.CharField(
        required=False, label="Withdraw Reject Reason", widget=forms.Textarea
    )

    class Meta:
        model = WithdrawApplication
        fields = ("status", "response")

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        response = cleaned_data.get("response")

        if status == WithdrawApplication.Statuses.REJECTED and not response:
            self.add_error("response", "This field is required when Withdrawal is refused")

        return cleaned_data


class ResponsePreparationBaseForm(forms.ModelForm):
    class Meta:
        fields = ("decision", "refuse_reason")
        widgets = {"refuse_reason": forms.Textarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["decision"].required = True

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        decision = cleaned_data.get("decision")
        refuse_reason = cleaned_data.get("refuse_reason")

        if decision == ApplicationBase.REFUSE and not refuse_reason:
            self.add_error(
                "refuse_reason", "This field is required when the Application is refused"
            )

        return cleaned_data


class ResponsePreparationImportForm(ResponsePreparationBaseForm):
    class Meta:
        model = ImportApplication
        fields = ResponsePreparationBaseForm.Meta.fields


class ResponsePreparationExportForm(ResponsePreparationBaseForm):
    class Meta:
        model = ExportApplication
        fields = ResponsePreparationBaseForm.Meta.fields


class ResponsePreparationVariationRequestImportForm(forms.ModelForm):
    class Meta:
        model = ImportApplication
        fields = ("decision", "variation_decision", "variation_refuse_reason")
        widgets = {"variation_refuse_reason": forms.Textarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["decision"].disabled = True

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        decision = cleaned_data.get("variation_decision")
        refuse_reason = cleaned_data.get("variation_refuse_reason")

        if decision == ApplicationBase.REFUSE and not refuse_reason:
            self.add_error(
                "variation_refuse_reason", "This field is required when the Application is refused"
            )

        return cleaned_data


class CaseEmailForm(forms.ModelForm):
    class Meta:
        model = CaseEmail
        fields = (
            "to",
            "cc_address_list",
            "subject",
            "attachments",
            "body",
        )
        widgets = {
            "body": forms.Textarea,
            "attachments": CheckboxSelectMultipleTable(attrs={"class": "radio-relative"}),
        }
        error_messages = {"cc_address_list": {"item_invalid": "Email number %(nth)s is not valid:"}}

    def __init__(self, *args: Any, case_email_config: CaseEmailConfig, **kwargs: Any):
        super().__init__(*args, **kwargs)

        if case_email_config.to_choices:
            self.fields["to"].widget = s2forms.Select2Widget(
                attrs={"data-placeholder": "Please choose a Recipient"},
                choices=case_email_config.to_choices,
            )

        if case_email_config.file_qs:
            self.fields["attachments"].required = False
            self.fields["attachments"].queryset = case_email_config.file_qs
            # set files and process on the widget to make them available in the widget's template
            self.fields["attachments"].widget.qs = case_email_config.file_qs
            self.fields["attachments"].widget.process = case_email_config.application
        else:
            self.fields.pop("attachments")


class CaseEmailResponseForm(forms.ModelForm):
    class Meta:
        model = CaseEmail
        fields = ("response",)


def application_contacts(application: ImpOrExp) -> QuerySet[User]:
    if application.is_import_application():
        org = application.agent or application.importer
    else:
        org = application.agent or application.exporter

    users = organisation_get_contacts(org)

    return users


class VariationRequestForm(forms.ModelForm):
    when_varied = JqueryDateField(
        required=True, label="What date would the varied licence(s) come into effect"
    )

    class Meta:
        model = VariationRequest
        fields = ("what_varied", "why_varied", "when_varied")

        widgets = {
            "what_varied": forms.Textarea({"rows": 4, "cols": 50}),
            "why_varied": forms.Textarea({"rows": 4, "cols": 50}),
        }


class VariationRequestCancelForm(forms.ModelForm):
    class Meta:
        model = VariationRequest
        fields = ("reject_cancellation_reason",)


class VariationRequestExportCancelForm(OptionalFormMixin, VariationRequestCancelForm):
    """Reuse the Variation Request Cancel form setting all fields as optional as they aren't required"""


class VariationRequestExportAppForm(forms.ModelForm):
    class Meta:
        model = VariationRequest
        fields = ("what_varied",)
        labels = {"what_varied": "Variation Reason"}

        widgets = {"what_varied": forms.Textarea({"rows": 4, "cols": 50})}


class RevokeApplicationForm(forms.Form):
    send_email = forms.BooleanField(
        required=False, label="Email Applicants?", widget=forms.CheckboxInput()
    )

    reason = forms.CharField(
        required=True, label="Reason", widget=forms.Textarea({"rows": 4, "cols": 50})
    )

    def __init__(self, *args, readonly_form: bool = False, **kwargs):
        super().__init__(*args, **kwargs)

        if readonly_form:
            for f in self.fields:
                self.fields[f].disabled = True


class ReassignOwnershipBaseForm(forms.ModelForm):
    email_assignee = forms.fields.BooleanField(
        required=False,
        widget=forms.CheckboxInput,
        help_text="Select to send an email to the person you are assigning the case to",
    )
    comment = forms.fields.CharField(
        max_length=250,
        widget=forms.Textarea,
        required=False,
        label="Add Comment",
        help_text="Text entered here will be added as a case note on the case and marked for attention",
    )

    class Meta:
        fields = ("case_owner", "email_assignee", "comment")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["case_owner"].queryset = get_all_case_officers().exclude(
            id=self.instance.case_owner_id
        )

    def clean_case_owner(self):
        case_owner = self.cleaned_data["case_owner"]

        if not case_owner:
            raise forms.ValidationError("Please select a user to reassign the case to.")

        return case_owner


class ReassignOwnershipImport(ReassignOwnershipBaseForm):
    class Meta:
        model = ImportApplication
        fields = ReassignOwnershipBaseForm.Meta.fields


class ReassignOwnershipExport(ReassignOwnershipBaseForm):
    class Meta:
        model = ExportApplication
        fields = ReassignOwnershipBaseForm.Meta.fields
