from typing import Any

from django.forms import CharField, Field, ModelChoiceField, ModelForm, Textarea

from web.domains.exporter.widgets import ExporterAgentWidget, ExporterWidget
from web.domains.importer.widgets import ImporterAgentWidget, ImporterWidget
from web.models import (
    AccessRequest,
    Exporter,
    ExporterAccessRequest,
    Importer,
    ImporterAccessRequest,
)


class AccessRequestFormBase(ModelForm):
    instance: ImporterAccessRequest | ExporterAccessRequest

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        request_type = cleaned_data.get("request_type")

        if request_type == self.instance.AGENT_ACCESS:
            if not cleaned_data.get("agent_name"):
                self.add_error("agent_name", Field.default_error_messages["required"])

            if not cleaned_data.get("agent_address"):
                self.add_error("agent_address", Field.default_error_messages["required"])
        else:
            cleaned_data["agent_name"] = ""
            cleaned_data["agent_address"] = ""

        return cleaned_data


class ExporterAccessRequestForm(AccessRequestFormBase):
    class Meta:
        model = ExporterAccessRequest

        fields = [
            "request_type",
            "organisation_name",
            "organisation_address",
            "organisation_registered_number",
            "agent_name",
            "agent_address",
        ]


class ImporterAccessRequestForm(AccessRequestFormBase):
    class Meta:
        model = ImporterAccessRequest

        fields = [
            "request_type",
            "organisation_name",
            "organisation_address",
            "organisation_registered_number",
            "eori_number",
            "request_reason",
            "agent_name",
            "agent_address",
        ]


class LinkOrgAccessRequestFormBase(ModelForm):
    instance: ImporterAccessRequest | ExporterAccessRequest

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        if self.instance.is_agent_request:
            link = cleaned_data.get("link")
            agent_link = cleaned_data.get("agent_link")

            if agent_link and agent_link.get_main_org() != link:
                self.add_error("agent_link", "Agent organisation is not linked to main org.")

        return cleaned_data


class LinkImporterAccessRequestForm(LinkOrgAccessRequestFormBase):
    link = ModelChoiceField(
        label="Link Importer",
        help_text=(
            "Search an importer to link."
            " Importers returned are matched against name, registerer number"
            ", eori number and user name/email."
        ),
        queryset=Importer.objects.filter(is_active=True, main_importer__isnull=True),
        widget=ImporterWidget,
    )

    agent_link = ModelChoiceField(
        label="Link Agent Importer",
        help_text=(
            "Search an agent importer to link."
            " Importers returned are matched against name, registerer number"
            ", eori number and user name/email."
        ),
        queryset=Importer.objects.filter(is_active=True, main_importer__isnull=False),
        widget=ImporterAgentWidget,
        required=False,
    )

    class Meta:
        model = ImporterAccessRequest
        fields = ["link", "agent_link"]


class LinkExporterAccessRequestForm(LinkOrgAccessRequestFormBase):
    link = ModelChoiceField(
        label="Link Exporter",
        help_text=(
            "Search an exporter to link."
            " Exporters returned are matched against name and registerer number."
        ),
        queryset=Exporter.objects.filter(is_active=True, main_exporter__isnull=True),
        widget=ExporterWidget,
    )

    agent_link = ModelChoiceField(
        label="Link Agent Exporter",
        help_text=(
            "Search an agent exporter to link."
            " Exporters returned are matched against name and registerer number."
        ),
        queryset=Exporter.objects.filter(is_active=True, main_exporter__isnull=False),
        widget=ExporterAgentWidget,
        required=False,
    )

    class Meta:
        model = ExporterAccessRequest
        fields = ["link", "agent_link"]


class CloseAccessRequestForm(ModelForm):
    response_reason = CharField(
        required=False,
        widget=Textarea,
        help_text="If refused please write the reason for the decision.",
    )

    class Meta:
        model = AccessRequest
        fields = ["response", "response_reason"]

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        response = cleaned_data.get("response")
        response_reason = cleaned_data.get("response_reason")

        if response == AccessRequest.REFUSED and response_reason == "":
            self.add_error(
                "response_reason", "This field is required when Access Request is refused"
            )

        if response == AccessRequest.APPROVED:
            if self.instance.is_agent_request and not self.instance.agent_link:
                self.add_error(
                    "response", "You must link an agent before approving the agent access request."
                )

        return cleaned_data
