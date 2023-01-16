from django.forms import ChoiceField, ModelChoiceField, ModelForm, Textarea
from guardian.shortcuts import get_users_with_perms

from web.domains.user.models import User
from web.flow.models import ProcessTypes

from .models import ApprovalRequest, ExporterApprovalRequest, ImporterApprovalRequest


class ExporterApprovalRequestForm(ModelForm):
    status = ChoiceField(
        choices=ApprovalRequest.STATUSES, initial=ApprovalRequest.DRAFT, disabled=True
    )
    requested_from = ModelChoiceField(
        queryset=User.objects.none(), empty_label="All", label="Contact", required=False
    )

    class Meta:
        model = ExporterApprovalRequest
        fields = ["status", "requested_from"]

    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application

        if self.application.link:
            users = get_users_with_perms(
                self.application.link, only_with_perms_in=["is_contact_of_exporter"]
            )
            self.fields["requested_from"].queryset = users

    def clean(self):
        self.instance.access_request = self.application
        self.instance.process_type = ProcessTypes.ExpApprovalReq
        return super().clean()


class ImporterApprovalRequestForm(ModelForm):
    status = ChoiceField(
        choices=ApprovalRequest.STATUSES, initial=ApprovalRequest.DRAFT, disabled=True
    )
    requested_from = ModelChoiceField(
        queryset=User.objects.none(), empty_label="All", label="Contact", required=False
    )

    class Meta:
        model = ImporterApprovalRequest
        fields = ["status", "requested_from"]

    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application

        if self.application.link:
            users = get_users_with_perms(
                self.application.link, only_with_perms_in=["is_contact_of_importer"]
            )
            self.fields["requested_from"].queryset = users

    def clean(self):
        self.instance.access_request = self.application
        self.instance.process_type = ProcessTypes.ImpApprovalReq
        return super().clean()


class ApprovalRequestResponseForm(ModelForm):
    class Meta:
        model = ApprovalRequest
        fields = ["response", "response_reason"]
        widgets = {"response_reason": Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["response"].required = True

    def clean(self):
        cleaned_data = super().clean()

        response = cleaned_data.get("response")
        reason = cleaned_data.get("response_reason")
        if response == ApprovalRequest.REFUSE and not reason:
            self.add_error("response_reason", "You must enter this item")
        else:
            cleaned_data["response_reason"] = ""

        return cleaned_data
