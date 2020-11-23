from django.forms import ChoiceField, ModelChoiceField, ModelForm
from guardian.shortcuts import get_users_with_perms

from web.domains.user.models import User

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

        users = get_users_with_perms(
            self.application.link, only_with_perms_in=["is_contact_of_exporter"]
        )
        self.fields["requested_from"].queryset = users

    def clean(self):
        self.instance.access_request = self.application
        self.instance.process_type = "ExporterApprovalRequest"
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

        users = get_users_with_perms(
            self.application.link, only_with_perms_in=["is_contact_of_importer"]
        )
        self.fields["requested_from"].queryset = users

    def clean(self):
        self.instance.access_request = self.application
        self.instance.process_type = "ImporterApprovalRequest"
        return super().clean()


class ApprovalRequestResponseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["response"].required = True

    class Meta:
        model = ApprovalRequest
        fields = ["response", "response_reason"]
