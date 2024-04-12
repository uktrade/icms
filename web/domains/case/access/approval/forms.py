from typing import Any

from django.forms import ChoiceField, ModelChoiceField, ModelForm, Textarea

from web.flow.models import ProcessTypes
from web.models import ExporterAccessRequest, ImporterAccessRequest, User
from web.permissions import get_org_obj_permissions, organisation_get_contacts

from .models import ApprovalRequest, ExporterApprovalRequest, ImporterApprovalRequest


class ExporterApprovalRequestForm(ModelForm):
    status = ChoiceField(
        choices=ApprovalRequest.Statuses.choices,
        initial=ApprovalRequest.Statuses.DRAFT,
        disabled=True,
    )
    requested_from = ModelChoiceField(
        queryset=User.objects.none(), empty_label="All", label="Contact", required=False
    )

    class Meta:
        model = ExporterApprovalRequest
        fields = ["status", "requested_from"]

    def __init__(self, *args: Any, access_request: ExporterAccessRequest, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.access_request = access_request

        if self.access_request.link:
            obj_perms = get_org_obj_permissions(self.access_request.link)
            users = organisation_get_contacts(
                self.access_request.link, perms=[obj_perms.manage_contacts_and_agents.codename]
            )
            self.fields["requested_from"].queryset = users

    def clean(self):
        self.instance.access_request = self.access_request
        self.instance.process_type = ProcessTypes.ExpApprovalReq
        return super().clean()


class ImporterApprovalRequestForm(ModelForm):
    status = ChoiceField(
        choices=ApprovalRequest.Statuses.choices,
        initial=ApprovalRequest.Statuses.DRAFT,
        disabled=True,
    )
    requested_from = ModelChoiceField(
        queryset=User.objects.none(), empty_label="All", label="Contact", required=False
    )

    class Meta:
        model = ImporterApprovalRequest
        fields = ["status", "requested_from"]

    def __init__(self, *args: Any, access_request: ImporterAccessRequest, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.access_request = access_request

        if self.access_request.link:
            obj_perms = get_org_obj_permissions(self.access_request.link)
            users = organisation_get_contacts(
                self.access_request.link, perms=[obj_perms.manage_contacts_and_agents.codename]
            )
            self.fields["requested_from"].queryset = users

    def clean(self):
        self.instance.access_request = self.access_request
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

        if response == ApprovalRequest.Responses.APPROVE:
            cleaned_data["response_reason"] = ""

        elif response == ApprovalRequest.Responses.REFUSE and not reason:
            self.add_error("response_reason", "You must enter this item")

        return cleaned_data
