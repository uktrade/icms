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


class LinkImporterAccessRequestForm(ModelForm):
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

    class Meta:
        model = ImporterAccessRequest
        fields = ["link"]


class LinkExporterAccessRequestForm(ModelForm):
    link = ModelChoiceField(
        label="Link Exporter",
        help_text=(
            "Search an exporter to link."
            " Exporters returned are matched against name and registerer number."
        ),
        queryset=Exporter.objects.filter(is_active=True, main_exporter__isnull=True),
        widget=ExporterWidget,
    )

    class Meta:
        model = ExporterAccessRequest
        fields = ["link"]


class LinkOrgAgentFormBase(ModelForm):
    instance: ImporterAccessRequest | ExporterAccessRequest

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        link = self.instance.link
        agent_link = cleaned_data.get("agent_link")

        if agent_link and agent_link.get_main_org() != link:
            self.add_error("agent_link", "Agent organisation is not linked to main organisation.")

        return cleaned_data


class LinkImporterAgentForm(LinkOrgAgentFormBase):
    class Meta:
        model = ImporterAccessRequest
        fields = ["agent_link"]

    agent_link = ModelChoiceField(
        label="Link Agent Importer",
        help_text=(
            "Search an agent importer to link."
            " Importers returned are matched against name, registerer number"
            ", eori number and user name/email."
        ),
        queryset=Importer.objects.none(),
        widget=ImporterAgentWidget(attrs={"data-minimum-input-length": 0}),
        required=True,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["agent_link"].queryset = Importer.objects.filter(
            is_active=True, main_importer=self.instance.link
        )


class LinkExporterAgentForm(LinkOrgAgentFormBase):
    class Meta:
        model = ExporterAccessRequest
        fields = ["agent_link"]

    agent_link = ModelChoiceField(
        label="Link Agent Exporter",
        help_text=(
            "Search an agent exporter to link."
            " Exporters returned are matched against name and registerer number."
        ),
        queryset=Exporter.objects.none(),
        widget=ExporterAgentWidget(attrs={"data-minimum-input-length": 0}),
        required=True,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["agent_link"].queryset = Exporter.objects.filter(
            is_active=True, main_exporter=self.instance.link
        )


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
