import structlog as logging
from django.forms import CharField, Field, ModelChoiceField, ModelForm, Textarea

from web.domains.exporter.widgets import ExporterWidget
from web.domains.importer.widgets import ImporterWidget
from web.models import (
    AccessRequest,
    Exporter,
    ExporterAccessRequest,
    Importer,
    ImporterAccessRequest,
)

logger = logging.getLogger(__name__)


class ExporterAccessRequestForm(ModelForm):
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

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get("request_type")
        if request_type == ExporterAccessRequest.AGENT_ACCESS:
            logger.debug("Validating agent")
            if not cleaned_data["agent_name"]:
                self.add_error("agent_name", Field.default_error_messages["required"])
            if not cleaned_data["agent_address"]:
                self.add_error("agent_address", Field.default_error_messages["required"])
        else:
            cleaned_data["agent_name"] = ""
            cleaned_data["agent_address"] = ""
        return cleaned_data


class ImporterAccessRequestForm(ModelForm):
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

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get("request_type")
        if request_type == ImporterAccessRequest.AGENT_ACCESS:
            logger.debug("Validating agent")
            if not cleaned_data["agent_name"]:
                self.add_error("agent_name", Field.default_error_messages["required"])
            if not cleaned_data["agent_address"]:
                self.add_error("agent_address", Field.default_error_messages["required"])
        else:
            cleaned_data["agent_name"] = ""
            cleaned_data["agent_address"] = ""
        return cleaned_data


class LinkImporterAccessRequestForm(ModelForm):
    link = ModelChoiceField(
        label="Link Importer",
        help_text="""
            Search an importer to link. Importers returned are matched against name, registerer number,
            eori number and user name/email.
        """,
        queryset=Importer.objects.filter(is_active=True),
        widget=ImporterWidget,
    )

    class Meta:
        model = ImporterAccessRequest
        fields = ["link"]


class LinkExporterAccessRequestForm(ModelForm):
    link = ModelChoiceField(
        label="Link Exporter",
        help_text="""
            Search an exporter to link. Exporters returned are matched against name and registerer number.
        """,
        queryset=Exporter.objects.filter(is_active=True),
        widget=ExporterWidget,
    )

    class Meta:
        model = ExporterAccessRequest
        fields = ["link"]


class CloseAccessRequestForm(ModelForm):
    response_reason = CharField(
        required=False,
        widget=Textarea,
        help_text="If refused please write the reason for the decision.",
    )

    class Meta:
        model = AccessRequest
        fields = ["response", "response_reason"]

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("response") == AccessRequest.REFUSED
            and cleaned_data.get("response_reason") == ""
        ):
            self.add_error(
                "response_reason", "This field is required when Access Request is refused"
            )
        return cleaned_data
